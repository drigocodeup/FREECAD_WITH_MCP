"""Real SDK protocol over TCP plus fail-closed HTTP/auth checks."""
import asyncio
from contextlib import contextmanager
import json
import math
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import threading
import time
from types import SimpleNamespace

import jwt
import pytest
import uvicorn
from cryptography.hazmat.primitives.asymmetric import rsa
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client
from starlette.testclient import TestClient
import httpx

from http_auth import OAuthJWTVerifier
from http_config import HTTPConfig
from server_http import create_http_app

PROJECT = Path(__file__).resolve().parents[1]
TOKEN = 'test-only-' + 'a' * 40


def config(**values):
    return HTTPConfig.from_env({'FREECAD_MCP_TOKEN': TOKEN, **values})


def test_config_defaults_and_secret_redaction():
    cfg = config()
    assert cfg.host == '127.0.0.1' and cfg.port == 8765
    assert TOKEN not in repr(cfg)
    assert cfg.url == 'http://127.0.0.1:8765/mcp'


@pytest.mark.parametrize('env', [
    {}, {'FREECAD_MCP_TOKEN':'short'}, {'FREECAD_MCP_AUTH_MODE':'none'},
    {'FREECAD_MCP_HOST':'0.0.0.0'}, {'FREECAD_MCP_PORT':'0'},
    {'FREECAD_MCP_PORT':'65536'}, {'FREECAD_MCP_ALLOWED_HOSTS':'*'},
    {'FREECAD_MCP_ALLOWED_ORIGINS':'https://*.example.com'},
    {'FREECAD_MCP_ALLOWED_ORIGINS':'https://example.com/path'},
    {'FREECAD_MCP_AUTH_MODE':'oauth'},
])
def test_bad_config(env):
    if env:
        env = {'FREECAD_MCP_TOKEN':TOKEN, **env}
    with pytest.raises(ValueError):
        HTTPConfig.from_env(env)


def test_explicit_nonlocal_opt_in():
    assert config(FREECAD_MCP_HOST='0.0.0.0',FREECAD_MCP_ALLOW_NON_LOOPBACK='1').host == '0.0.0.0'


def test_http_auth_host_origin_and_body_limit():
    with TestClient(create_http_app(config()),base_url='http://127.0.0.1:8765') as client:
        for headers in ({}, {'Authorization':'Bearer wrong'},
                        [('Authorization','Bearer '+TOKEN),('Authorization','Bearer '+TOKEN)]):
            response = client.post('/mcp',headers=headers,json={})
            assert response.status_code == 401
            assert 'Bearer' in response.headers['www-authenticate']
        headers = {'Authorization':'Bearer '+TOKEN,'Accept':'application/json, text/event-stream'}
        assert client.post('/mcp',headers={**headers,'Host':'evil.example'},json={}).status_code == 421
        for origin in ('https://evil.example','null','http://localhost:9999'):
            assert client.post('/mcp',headers={**headers,'Origin':origin},json={}).status_code == 403
        request = {'jsonrpc':'2.0','id':1,'method':'initialize','params':{
            'protocolVersion':'2025-11-25','capabilities':{},'clientInfo':{'name':'test','version':'1'}}}
        for origin in (None,'http://localhost:8765'):
            h = {**headers, **({'Origin':origin} if origin else {})}
            assert client.post('/mcp',headers=h,json=request).status_code == 200
        assert client.post('/mcp',headers={**headers,'Content-Type':'application/json'},content='x'*65537).status_code == 413


def oauth_config():
    return config(FREECAD_MCP_AUTH_MODE='oauth',FREECAD_MCP_OAUTH_ISSUER='https://issuer.example/',
                  FREECAD_MCP_OAUTH_JWKS_URL='https://issuer.example/jwks',
                  FREECAD_MCP_RESOURCE_URL='https://cad.example/mcp')


def test_oauth_signature_issuer_audience_expiry_and_scope():
    cfg = oauth_config()
    assert cfg.issuer == 'https://issuer.example/'
    key = rsa.generate_private_key(public_exponent=65537,key_size=2048)
    jwks = SimpleNamespace(get_signing_key_from_jwt=lambda _: SimpleNamespace(key=key.public_key()))
    verifier = OAuthJWTVerifier(cfg,jwks)
    now = int(time.time())
    claims = dict(iss=cfg.issuer,aud=cfg.audience,sub='user',iat=now,exp=now+600,scope='freecad:control')
    def token(**changes):
        return jwt.encode({**claims,**changes},key,algorithm='RS256')
    assert asyncio.run(verifier.verify_token(token())).scopes == ['freecad:control']
    for bad in (token(iss='https://other/'),token(aud='other'),token(exp=now-60),
                jwt.encode(claims,'test-only-key-'+'x'*40,algorithm='HS256'),'malformed'):
        assert asyncio.run(verifier.verify_token(bad)) is None
    other = rsa.generate_private_key(public_exponent=65537,key_size=2048)
    assert asyncio.run(verifier.verify_token(jwt.encode(claims,other,algorithm='RS256'))) is None
    with TestClient(create_http_app(cfg,verifier),base_url='http://127.0.0.1:8765') as client:
        metadata = client.get('/.well-known/oauth-protected-resource/mcp')
        assert metadata.status_code == 200
        assert metadata.json()['authorization_servers'] == [cfg.issuer]
        assert client.post('/mcp',json={}).status_code == 401
        headers = {'Authorization':'Bearer '+token(scope='read'),'Accept':'application/json, text/event-stream'}
        assert client.post('/mcp',headers=headers,json={}).status_code == 403
        headers['Authorization'] = 'Bearer '+token()
        # Auth succeeds; invalid JSON-RPC payload is rejected by the MCP layer.
        assert client.post('/mcp',headers=headers,json={}).status_code == 400


@contextmanager
def running_http():
    """A real loopback listener; only this fixture's server is stopped."""
    sock = socket.socket()
    sock.bind(('127.0.0.1',0))
    port = sock.getsockname()[1]
    secret = secrets.token_urlsafe(48)
    cfg = HTTPConfig.from_env({'FREECAD_MCP_TOKEN':secret,'FREECAD_MCP_PORT':str(port)})
    server = uvicorn.Server(uvicorn.Config(create_http_app(cfg),log_level='error',access_log=False))
    thread = threading.Thread(target=server.run,kwargs={'sockets':[sock]},daemon=True)
    thread.start()
    try:
        deadline = time.monotonic()+10
        while not server.started:
            if not thread.is_alive() or time.monotonic()>deadline:
                raise RuntimeError('HTTP test server did not start')
            time.sleep(.02)
        yield cfg.url,secret
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        sock.close()
        assert not thread.is_alive()


def test_real_http_protocol_matches_stdio():
    with running_http() as (url,secret):
        async def run():
            params = StdioServerParameters(command=sys.executable,args=[str(PROJECT/'server.py')])
            async with stdio_client(params) as (r,w):
                async with ClientSession(r,w) as stdio:
                    await stdio.initialize()
                    local = await stdio.list_tools()
            async with httpx.AsyncClient(headers={'Authorization':'Bearer '+secret}) as client:
                async with streamable_http_client(url,http_client=client) as (r,w,_):
                    async with ClientSession(r,w) as session:
                        await session.initialize()
                        remote = await session.list_tools()
                        assert len(remote.tools) == 36
                        assert [t.model_dump() for t in remote.tools] == [t.model_dump() for t in local.tools]
                        invalid = await session.call_tool('freecad_create_box',{'document':'Missing'})
                        assert invalid.isError
                        arbitrary = await session.call_tool('execute_python',{'code':'raise RuntimeError()'})
                        assert arbitrary.isError
        asyncio.run(run())


def test_http_entry_point_uses_environment_and_requires_secret():
    env = {k:v for k,v in os.environ.items() if not k.startswith('FREECAD_MCP_')}
    failed = subprocess.run([sys.executable,str(PROJECT/'server_http.py')],env=env,
                            capture_output=True,text=True,timeout=10)
    assert failed.returncode == 2 and 'FREECAD_MCP_TOKEN' in failed.stderr
    with socket.socket() as reservation:
        reservation.bind(('127.0.0.1',0))
        port = reservation.getsockname()[1]
    secret = secrets.token_urlsafe(48)
    env.update(FREECAD_MCP_TOKEN=secret,FREECAD_MCP_PORT=str(port))
    process = subprocess.Popen([sys.executable,str(PROJECT/'server_http.py')],env=env,
                               stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        deadline = time.monotonic()+10
        while True:
            assert process.poll() is None,'HTTP entry point exited early'
            try:
                response = httpx.post(f'http://127.0.0.1:{port}/mcp',json={},timeout=.5,trust_env=False)
                assert response.status_code == 401
                break
            except (httpx.ConnectError,httpx.ConnectTimeout):
                assert time.monotonic()<deadline,'HTTP entry point did not bind configured port'
                time.sleep(.02)
    finally:
        process.terminate()
        out,err = process.communicate(timeout=10)
        assert secret not in out+err


@pytest.mark.skipif(sys.platform!='win32',reason='Windows PowerShell launcher')
def test_powershell_stdio_launcher():
    if not (PROJECT/'.venv/Scripts/python.exe').exists():
        pytest.skip('Install project venv to exercise PowerShell launcher')
    async def run():
        params = StdioServerParameters(command='powershell.exe',args=[
            '-NoProfile','-ExecutionPolicy','Bypass','-File',str(PROJECT/'scripts/start-stdio.ps1')])
        async with stdio_client(params) as (r,w):
            async with ClientSession(r,w) as session:
                await session.initialize()
                assert len((await session.list_tools()).tools)==36
    asyncio.run(run())


@pytest.mark.integration
@pytest.mark.skipif(os.environ.get('FREECAD_INTEGRATION')!='1',reason='Requires real FreeCAD GUI bridge')
def test_real_http_cad_roundtrip():
    with running_http() as (url,secret):
        async def run():
            report = {'transport':'streamable-http','calls':[]}
            async with httpx.AsyncClient(headers={'Authorization':'Bearer '+secret}) as client:
                async with streamable_http_client(url,http_client=client) as (r,w,_):
                    async with ClientSession(r,w) as session:
                        await session.initialize()
                        async def call(op,**args):
                            result = await session.call_tool('freecad_'+op,args)
                            assert not result.isError,str(result.content)
                            data = result.structuredContent or json.loads(result.content[0].text)
                            report['calls'].append({'tool':op,'arguments':args,'result':data})
                            return data
                        assert (await call('health_check'))['gui']
                        name = 'HTTP_' + str(time.time_ns())
                        await call('new_document',name=name)
                        await call('create_box',document=name,name='Base',length=40,width=30,height=6)
                        await call('create_cylinder',document=name,name='Furo',radius=3,height=8,position=[20,15,-1])
                        cut = await call('boolean_cut',document=name,name='Peca',base='Base',tool='Furo')
                        expected = 7200-math.pi*9*6
                        assert cut['valid'] and cut['solids']==1
                        assert math.isclose(cut['volume_mm3'],expected,rel_tol=1e-10)
                        await call('validate_shape',document=name,object_name='Peca')
                        assert (await call('get_bounding_box',document=name,object_name='Peca'))['bounding_box']['size']==[40,30,6]
                        forbidden = await session.call_tool('freecad_save_fcstd',{'document':name,'filename':'../escape.FCStd'})
                        assert forbidden.isError
                        await call('set_view',document=name,view='isometric')
                        await call('fit_all',document=name)
                        for op,ext in [('save_fcstd','.FCStd'),('export_step','.step'),('export_stl','.stl'),('capture_view','.png')]:
                            args = dict(document=name,filename=name+ext)
                            if op.startswith('export_'): args['object_names']=['Peca']
                            saved = await call(op,**args)
                            assert Path(saved['path']).stat().st_size>0
                        await call('close_document',document=name,discard=True)
                        reopened = await call('open_document',filename=name+'.FCStd')
                        shape = await call('validate_shape',document=reopened['document'],object_name='Peca')
                        assert shape['valid'] and shape['solids']==1
                        assert math.isclose(shape['volume_mm3'],expected,rel_tol=1e-10)
                        report.update(passed=True,expected_volume_mm3=expected,actual_volume_mm3=shape['volume_mm3'])
            (PROJECT/'http-integration-result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        asyncio.run(run())
