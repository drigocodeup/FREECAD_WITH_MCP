"""Exercise the real graphical document over both official MCP transports."""
import asyncio,json,os,sys,time
from pathlib import Path
import httpx,pytest
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client
from test_http import running_http
from cess_gui.electrical_model import wire_points

PROJECT=Path(__file__).resolve().parents[1]
pytestmark=[pytest.mark.integration,pytest.mark.skipif(os.environ.get('FREECAD_INTEGRATION')!='1',reason='Requires real FreeCAD GUI')]

@pytest.mark.parametrize('transport',['stdio','http'])
def test_electrical_real_roundtrip(transport):
    async def exercise(session):
        await session.initialize()
        assert len((await session.list_tools()).tools)==43
        calls=[]
        async def call(op,**args):
            result=await session.call_tool('freecad_'+op,args)
            assert not result.isError,str(result.content)
            calls.append(op)
            return result.structuredContent or json.loads(result.content[0].text)
        catalog=await call('electrical_catalog')
        assert len(catalog['symbols'])==17 and catalog['simulation'] is False
        name='Eletrica_'+transport+'_'+str(time.time_ns())
        await call('new_document',name=name)
        sheet=await call('electrical_create_sheet',document=name,name='Comando',paper='A4',orientation='portrait')
        args=dict(document=name,sheet=sheet['sheet'])
        first=await call('electrical_add_symbol',**args,kind='contact_no',x=70,y=70,tag='KM1')
        second=await call('electrical_add_symbol',**args,kind='coil',x=70,y=130,tag='KM1')
        await call('electrical_add_wire',**args,start={'symbol':first['symbol_id'],'pin':'14'},end={'symbol':second['symbol_id'],'pin':'A1'},label='1')
        state=await call('electrical_get_sheet',**args)
        state['drawing']['symbols'][0]['x']=90
        state['drawing']['metadata']['author']='Teste MCP '+transport
        updated=await call('electrical_update_sheet',**args,drawing=state['drawing'])
        assert wire_points(updated['drawing'],updated['drawing']['wires'][0])[0]==[90,80]
        bad=await session.call_tool('freecad_electrical_add_symbol',{**args,'kind':'coil','x':5,'y':280})
        assert bad.isError
        bad=await session.call_tool('freecad_electrical_add_wire',{**args,'start':{'symbol':first['symbol_id'],'pin':'invalid'},'end':{'point':[100,100]}})
        assert bad.isError
        assert (await call('electrical_get_sheet',**args))['symbol_count']==2
        assert (await session.call_tool('freecad_electrical_export_sheet',{**args,'filename':'../escape.pdf'})).isError
        outputs=[]
        for extension in ('.pdf','.svg','.png','.json'):
            saved=await call('electrical_export_sheet',**args,filename=name+extension)
            assert Path(saved['path']).stat().st_size>0
            outputs.append(saved['path'])
        await call('save_fcstd',document=name,filename=name+'.FCStd')
        await call('close_document',document=name,discard=True)
        reopened=await call('open_document',filename=name+'.FCStd')
        actual=await call('electrical_get_sheet',document=reopened['document'],sheet=args['sheet'])
        assert actual['drawing']==updated['drawing'] and actual['wire_count']==1
        await call('close_document',document=reopened['document'],discard=True)
        (PROJECT/('electrical-'+transport+'-validation.json')).write_text(json.dumps(dict(passed=True,transport=transport,calls=calls,outputs=outputs),indent=2),encoding='utf-8')
    async def run_stdio():
        async with stdio_client(StdioServerParameters(command=sys.executable,args=[str(PROJECT/'server.py')])) as (r,w):
            async with ClientSession(r,w) as session:await exercise(session)
    async def run_http(url,secret):
        async with httpx.AsyncClient(headers={'Authorization':'Bearer '+secret},timeout=httpx.Timeout(120)) as client:
            async with streamable_http_client(url,http_client=client) as (r,w,_):
                async with ClientSession(r,w) as session:await exercise(session)
    if transport=='stdio':asyncio.run(run_stdio())
    else:
        with running_http() as (url,secret):asyncio.run(run_http(url,secret))
