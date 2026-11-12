import asyncio,json,os,sys,time
from pathlib import Path
import pytest,httpx
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client
from test_http import running_http
PROJECT=Path(__file__).resolve().parents[1]


@pytest.mark.integration
@pytest.mark.skipif(os.environ.get('FREECAD_INTEGRATION')!='1',reason='Requires real GUI bridge')
def test_real_fasteners_both_transports():
    report={'passed':False,'cases':[]}
    async def exercise(session,transport,head):
        await session.initialize()
        calls=[]
        async def call(op,**args):
            result=await session.call_tool('freecad_'+op,args)
            assert not result.isError,str(result.content)
            data=result.structuredContent or json.loads(result.content[0].text)
            calls.append(dict(tool=op,arguments=args,result=data))
            return data
        name='Fixador_'+head+'_'+str(time.time_ns())
        prefix='parafusos_porcas/'+name
        await call('new_document',name=name)
        output=await call('generate_fastener',document=name,name='Fixador',head_type=head)
        assert len(output['objects'])==2
        names=[o['name'] for o in output['objects']]
        for name_obj in names:
            shape=await call('validate_shape',document=name,object_name=name_obj)
            assert shape['valid'] and shape['solids']==1
        bad=await session.call_tool('freecad_generate_fastener',dict(document=name,name='Invalid',head_type='torx'))
        assert bad.isError
        await call('set_view',document=name,view='isometric')
        await call('fit_all',document=name)
        await call('capture_view',document=name,filename=prefix+'.png',width=1400,height=1000)
        await call('save_fcstd',document=name,filename=prefix+'.FCStd')
        await call('export_step',document=name,object_names=names,filename=prefix+'.step')
        for obj in names:
            await call('export_stl',document=name,object_names=[obj],filename=prefix+'_'+obj+'.stl')
        await call('close_document',document=name,discard=True)
        reopened=await call('open_document',filename=prefix+'.FCStd')
        for obj in names:
            assert (await call('validate_shape',document=reopened['document'],object_name=obj))['valid']
        report['cases'].append(dict(transport=transport,head=head,prefix=prefix,calls=calls))
    async def run():
        params=StdioServerParameters(command=sys.executable,args=[str(PROJECT/'server.py')])
        async with stdio_client(params) as (r,w):
            async with ClientSession(r,w) as session: await exercise(session,'stdio','allen')
        with running_http() as (url,token):
            async with httpx.AsyncClient(headers={'Authorization':'Bearer '+token},timeout=httpx.Timeout(120,connect=10)) as client:
                async with streamable_http_client(url,http_client=client) as (r,w,_):
                    async with ClientSession(r,w) as session: await exercise(session,'streamable-http','sextavada')
    asyncio.run(run())
    report['passed']=True
    (PROJECT/'fastener-mcp-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
