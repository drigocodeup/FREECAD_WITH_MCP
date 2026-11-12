import asyncio
import json
import os
from pathlib import Path
import sys
import time
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROJECT = Path(__file__).resolve().parents[1]


@pytest.mark.integration
@pytest.mark.skipif(os.environ.get('FREECAD_INTEGRATION') != '1',reason='Requires real FreeCAD bridge')
def test_five_generators_over_real_mcp():
    async def run():
        params = StdioServerParameters(command=sys.executable,args=[str(PROJECT/'server.py')])
        report = {'calls':[]}
        async with stdio_client(params) as (reader,writer):
            async with ClientSession(reader,writer) as session:
                await session.initialize()
                async def call(tool,**kwargs):
                    r = await session.call_tool('freecad_'+tool,kwargs)
                    assert not r.isError,str(r.content)
                    result = r.structuredContent or json.loads(r.content[0].text)
                    report['calls'].append({'tool':'freecad_'+tool,'arguments':kwargs,'result':result})
                    return result
                document = (await call('new_document',name='MCP_Geradores_'+str(int(time.time()))))['document']
                tools = ['generate_gear','generate_box_with_lid','generate_channel_letters',
                         'generate_channel_numbers','generate_organizer']
                for index,tool in enumerate(tools):
                    result = await call(tool,document=document,name='TesteGerador'+str(index))
                    assert result['objects'] and all(o['valid'] and o['solids']>=1 for o in result['objects'])
                invalid = await session.call_tool('freecad_generate_channel_numbers',
                                                 {'document':document,'name':'Invalido','text':'ABC'})
                assert invalid.isError
                objects = await call('list_objects',document=document)
                assert not any(o['name']=='Invalido' for o in objects['objects'])
                await call('save_fcstd',document=document,filename=document+'.FCStd')
                await call('close_document',document=document)
        report['passed'] = True
        (PROJECT/'generators-mcp-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    asyncio.run(run())
