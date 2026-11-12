import asyncio
import json
import os
from pathlib import Path
import sys
import time
import pytest
import httpx
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client
from test_http import running_http

PROJECT=Path(__file__).resolve().parents[1]


@pytest.mark.integration
@pytest.mark.skipif(os.environ.get('FREECAD_INTEGRATION')!='1',reason='Requires real GUI bridge')
def test_gear_pairs_both_transports():
    report={'passed':False,'cases':[]}
    async def exercise(session,transport,ratio):
        await session.initialize()
        calls=[]
        async def call(op,**args):
            r=await session.call_tool('freecad_'+op,args)
            assert not r.isError,str(r.content)
            data=r.structuredContent or json.loads(r.content[0].text)
            calls.append(dict(tool=op,arguments=args,result=data))
            return data
        label='Reducao' if ratio=='2:1' else 'Aumento'
        name=label+'_'+str(time.time_ns())
        prefix='conjuntos_engrenagens/'+name
        await call('new_document',name=name)
        result=await call('generate_gear_pair',document=name,name='Conjunto',ratio=ratio)
        assert len(result['objects'])==6
        info=result['transmission']
        assert (info['input_teeth'],info['output_teeth'])==((20,40) if ratio=='2:1' else (40,20))
        names=[o['name'] for o in result['objects']]
        for n in names:
            shape=await call('validate_shape',document=name,object_name=n)
            assert shape['valid'] and shape['solids']==1
        invalid=await session.call_tool('freecad_generate_gear_pair',dict(document=name,name='Invalid',ratio='100:1'))
        assert invalid.isError
        await call('set_view',document=name,view='isometric')
        await call('fit_all',document=name)
        await call('capture_view',document=name,filename=prefix+'.png',width=1500,height=1000)
        await call('save_fcstd',document=name,filename=prefix+'.FCStd')
        await call('export_step',document=name,object_names=names,filename=prefix+'.step')
        await call('export_stl',document=name,object_names=names,filename=prefix+'.stl')
        for n in names:
            await call('export_stl',document=name,object_names=[n],filename=prefix+'_'+n+'.stl')
        await call('close_document',document=name,discard=True)
        reopened=await call('open_document',filename=prefix+'.FCStd')
        for n in names:
            assert (await call('validate_shape',document=reopened['document'],object_name=n))['valid']
        report['cases'].append(dict(transport=transport,ratio=ratio,prefix=prefix,calls=calls))
    async def run():
        params=StdioServerParameters(command=sys.executable,args=[str(PROJECT/'server.py')])
        async with stdio_client(params) as (r,w):
            async with ClientSession(r,w) as session:
                await exercise(session,'stdio','2:1')
        with running_http() as (url,secret):
            async with httpx.AsyncClient(headers={'Authorization':'Bearer '+secret},timeout=httpx.Timeout(120,connect=10)) as client:
                async with streamable_http_client(url,http_client=client) as (r,w,_):
                    async with ClientSession(r,w) as session:
                        await exercise(session,'streamable-http','1:2')
    asyncio.run(run())
    report['passed']=True
    (PROJECT/'gear-pair-mcp-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
