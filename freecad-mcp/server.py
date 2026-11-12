"""MCP STDIO entry point. Never print to stdout."""
import logging
import sys
from mcp.server.fastmcp import FastMCP
from tools import documents, primitives, boolean, transformations, inspection, exporters, visualization

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
mcp = FastMCP("freecad_local", instructions="Controle local do FreeCAD em mm. Inicie o bridge antes das chamadas. Use os nomes Name retornados. Salve/exporte somente em modelos. Valide solidos apos alteracoes. Nunca repita uma mutacao que sofreu timeout sem inspecionar o documento.")
for module in (documents, primitives, boolean, transformations, inspection, exporters, visualization):
    module.register(mcp)

if __name__ == "__main__":
    mcp.run(transport="stdio")
