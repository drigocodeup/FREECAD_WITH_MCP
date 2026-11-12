import asyncio
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROJECT = Path(__file__).resolve().parents[1]


def test_real_stdio_catalog_and_validation():
    async def run():
        params = StdioServerParameters(command=sys.executable, args=[str(PROJECT / 'server.py')])
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                catalog = await session.list_tools()
                assert len(catalog.tools) == 36
                assert any(t.name == 'freecad_generate_fastener' for t in catalog.tools)
                assert any(t.name == 'freecad_generate_gear_pair' for t in catalog.tools)
                assert any(t.name == 'freecad_generate_gear' for t in catalog.tools)
                assert any(t.name == 'freecad_boolean_cut' for t in catalog.tools)
                result = await session.call_tool('freecad_create_box', {'document': 'Missing'})
                assert result.isError
    asyncio.run(run())
