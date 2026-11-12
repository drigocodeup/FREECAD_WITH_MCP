"""Real MCP -> GUI bridge -> OCCT -> files. No mocks."""
import asyncio
import json
import math
import os
from pathlib import Path
import sys
import time
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROJECT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.integration


async def exercise():
    report = {'started': time.strftime('%Y-%m-%dT%H:%M:%S'), 'calls': []}
    params = StdioServerParameters(command=sys.executable, args=[str(PROJECT / 'server.py')])
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            async def call(op, **kwargs):
                result = await session.call_tool('freecad_' + op, kwargs)
                if result.isError:
                    raise AssertionError(f'{op}: {result.content}')
                data = result.structuredContent
                if data is None:
                    data = json.loads(result.content[0].text)
                report['calls'].append({'tool': 'freecad_' + op, 'arguments': kwargs, 'result': data})
                return data
            health = await call('health_check')
            assert health['gui']
            name = 'TesteMCP'
            docs = await call('list_documents')
            if any(d['name'] == name for d in docs['documents']):
                name += '_' + str(int(time.time()))
            filename = name
            if (PROJECT.parent / 'modelos' / (filename + '.FCStd')).exists():
                filename += '_' + str(int(time.time()))
            await call('new_document', name=name)
            await call('create_box', document=name, name='Caixa', length=100, width=60, height=20)
            await call('create_cylinder', document=name, name='Cilindro', radius=8, height=30)
            await call('move_object', document=name, object_name='Cilindro', position=[50, 30, -5])
            cut = await call('boolean_cut', document=name, name='PlacaFurada', base='Caixa', tool='Cilindro')
            assert cut['valid'] and cut['solids'] == 1
            expected = 120000 - math.pi * 8**2 * 20
            assert math.isclose(cut['volume_mm3'], expected, rel_tol=1e-10)
            await call('validate_shape', document=name, object_name='PlacaFurada')
            await call('set_view', document=name, view='isometric')
            await call('fit_all', document=name)
            await call('capture_view', document=name, filename=filename + '.png')
            await call('save_fcstd', document=name, filename=filename + '.FCStd')
            await call('export_step', document=name, object_names=['PlacaFurada'], filename=filename + '.step')
            await call('export_stl', document=name, object_names=['PlacaFurada'], filename=filename + '.stl')
            await call('close_document', document=name, discard=True)
            reopened = await call('open_document', filename=filename + '.FCStd')
            final = await call('get_object_properties', document=reopened['document'], object_name='PlacaFurada')
            assert final['valid'] and final['solids'] == 1
            assert math.isclose(final['volume_mm3'], expected, rel_tol=1e-10)
            assert set(final['dependencies']) == {'Caixa', 'Cilindro'}
            report['expected_volume_mm3'] = expected
            report['actual_volume_mm3'] = final['volume_mm3']
            report['filename'] = filename
            report['passed'] = True
    (PROJECT / 'integration-result.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


@pytest.mark.skipif(os.environ.get('FREECAD_INTEGRATION') != '1', reason='Requires real FreeCAD GUI bridge')
def test_real_cad_roundtrip():
    asyncio.run(exercise())


@pytest.mark.skipif(os.environ.get('FREECAD_INTEGRATION') != '1', reason='Requires real FreeCAD GUI bridge')
def test_remaining_tools_and_rejections():
    async def run():
        params = StdioServerParameters(command=sys.executable, args=[str(PROJECT / 'server.py')])
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                async def call(op, **kwargs):
                    result = await session.call_tool('freecad_' + op, kwargs)
                    assert not result.isError, str(result.content)
                    return result.structuredContent or json.loads(result.content[0].text)
                name = 'Ferramentas_' + str(int(time.time()))
                await call('new_document', name=name)
                await call('create_box', document=name, name='A', length=10, width=10, height=10)
                await call('create_sphere', document=name, name='Esfera', radius=3, position=[30, 0, 0])
                await call('create_cone', document=name, name='Cone', radius1=5, radius2=0, height=10, position=[50, 0, 0])
                await call('create_torus', document=name, name='Toro', radius1=8, radius2=2, position=[80, 0, 0])
                await call('create_box', document=name, name='B', length=10, width=10, height=10, position=[5, 0, 0])
                union = await call('boolean_union', document=name, name='Uniao', base='A', tool='B')
                assert math.isclose(union['volume_mm3'], 1500)
                intersection = await call('boolean_intersection', document=name, name='Comum', base='A', tool='B')
                assert math.isclose(intersection['volume_mm3'], 500)
                await call('rotate_object', document=name, object_name='Cone', axis=[0, 1, 0], angle=90)
                await call('copy_object', document=name, object_name='Esfera', name='Copia')
                await call('move_object', document=name, object_name='Copia', position=[30, 20, 0])
                vol = await call('get_volume', document=name, object_name='Copia')
                assert math.isclose(vol['volume_mm3'], 4/3 * math.pi * 27)
                bbox = await call('get_bounding_box', document=name, object_name='A')
                assert bbox['bounding_box']['size'] == [10, 10, 10]
                for op, kwargs in [
                    ('delete_object', {'object_name': 'A'}),
                    ('save_document', {'filename': '../escape.FCStd'}),
                    ('create_box', {'name': 'Invalido', 'length': -1, 'width': 1, 'height': 1}),
                    ('close_document', {})]:
                    result = await session.call_tool('freecad_' + op, {'document': name, **kwargs})
                    assert result.isError, op
                objects = await call('list_objects', document=name)
                assert not any(o['name'] == 'Invalido' for o in objects['objects'])
                await call('delete_object', document=name, object_name='Copia')
                await call('save_document', document=name, filename=name + '.FCStd')
                # No view/geometry changes since save: default close must succeed.
                await call('close_document', document=name)
    asyncio.run(run())


if __name__ == '__main__':
    print(json.dumps(asyncio.run(exercise()), indent=2))
