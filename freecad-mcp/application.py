"""Single tool catalog shared by the STDIO and Streamable HTTP entry points."""
from mcp.server.fastmcp import FastMCP
from tools import documents, primitives, boolean, transformations, inspection, exporters, visualization, generators

INSTRUCTIONS = ('Controle local do FreeCAD em mm. Inicie o bridge antes das chamadas. '
                'Use os nomes Name retornados. Salve/exporte somente em modelos. '
                'Valide solidos apos alteracoes. Nunca repita uma mutacao que sofreu timeout '
                'sem inspecionar o documento. Nao existe ferramenta para executar Python arbitrario.')


def create_server(**settings):
    server = FastMCP('freecad_local',instructions=INSTRUCTIONS,**settings)
    for module in (documents,primitives,boolean,transformations,inspection,exporters,visualization,generators):
        module.register(server)
    return server
