from pathlib import Path
root=Path('freecad-mcp')
(root/'tools').mkdir(exist_ok=True)
(root/'tools/__init__.py').write_text('')
groups={
'documents': {
'health_check': ('', 'Consulta versao, GUI, documentos e disponibilidade do bridge.'),
'new_document': ('name: str', 'Cria documento vazio com nome exclusivo.'),
'open_document': ('filename: str', 'Abre FCStd dentro da pasta modelos.'),
'list_documents': ('', 'Lista documentos abertos.'),
'save_document': ('document: str, filename: str, overwrite: bool = False', 'Salva documento FCStd em modelos; nao sobrescreve por padrao.'),
'close_document': ('document: str, discard: bool = False', 'Fecha documento; exige descarte explicito se modificado.')},
'primitives': {
'create_box': ('document: str, name: str, length: float, width: float, height: float, position: list[float] = [0, 0, 0]', 'Cria caixa parametrica; dimensoes positivas em mm e posicao absoluta XYZ.'),
'create_cylinder': ('document: str, name: str, radius: float, height: float, position: list[float] = [0, 0, 0]', 'Cria cilindro parametrico ao longo de Z; raio e altura em mm.'),
'create_sphere': ('document: str, name: str, radius: float, position: list[float] = [0, 0, 0]', 'Cria esfera parametrica; raio em mm.'),
'create_cone': ('document: str, name: str, radius1: float, radius2: float, height: float, position: list[float] = [0, 0, 0]', 'Cria cone ao longo de Z; permite um raio zero; medidas em mm.'),
'create_torus': ('document: str, name: str, radius1: float, radius2: float, position: list[float] = [0, 0, 0]', 'Cria toro parametrico; raio maior deve exceder raio do tubo, em mm.')},
'boolean': {op: ('document: str, name: str, base: str, tool: str', desc) for op,desc in [('boolean_union','Une solidos, preservando referencias Base e Tool.'),('boolean_cut','Subtrai Tool de Base, preservando referencias parametricas.'),('boolean_intersection','Calcula intersecao solida de Base e Tool.')]},
 'transformations': {
'move_object': ('document: str, object_name: str, position: list[float]', 'Define posicao absoluta XYZ em mm; preserva rotacao.'),
'rotate_object': ('document: str, object_name: str, axis: list[float], angle: float', 'Define rotacao absoluta no eixo XYZ, angulo em graus; preserva translacao.'),
'copy_object': ('document: str, object_name: str, name: str', 'Cria copia vinculada App::Link preservando referencia ao original.'),
'delete_object': ('document: str, object_name: str', 'Remove objeto somente se nao possui dependentes.')},
'inspection': {**{'list_objects': ('document: str', 'Lista objetos e dependencias.')}, **{op: ('document: str, object_name: str', desc) for op,desc in [('get_object_properties','Consulta propriedades e geometria.'),('get_bounding_box','Consulta limites XYZ e dimensoes em mm.'),('get_volume','Consulta volume em mm cubicos.'),('validate_shape','Recalcula e verifica validade, quantidade de solidos e volume.')] }},
'exporters': {**{op: ('document: str, object_names: list[str], filename: str, overwrite: bool = False', desc) for op,desc in [('export_step','Exporta objetos selecionados para .step em modelos.'),('export_stl','Exporta objetos selecionados para .stl em modelos, coordenadas em mm.')]}, 'save_fcstd': ('document: str, filename: str, overwrite: bool = False', 'Salva projeto nativo FCStd em modelos.')},
'visualization': {
'fit_all': ('document: str', 'Enquadra todos os objetos na vista.'),
'set_view': ('document: str, view: str', 'Seleciona isometric, front, rear, top, bottom, left ou right.'),
'capture_view': ('document: str, filename: str, width: int = 1200, height: int = 800, overwrite: bool = False', 'Captura vista GUI para PNG em modelos; dimensoes de 64 a 4096 pixels.')}
}
for module, funcs in groups.items():
    out='from bridge.client import call\n\n\ndef register(mcp):\n'
    for name,(sig,desc) in funcs.items():
        out+=f'    @mcp.tool()\n    def freecad_{name}({sig}) -> dict:\n        """{desc}"""\n        return call("{name}", locals())\n\n'
    (root/f'tools/{module}.py').write_text(out,encoding='utf-8')
(root/'server.py').write_text('''"""MCP STDIO entry point. Never print to stdout."""
import logging
import sys
from application import create_server

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
mcp = create_server()

if __name__ == "__main__":
    mcp.run(transport="stdio")
''',encoding='utf-8')
