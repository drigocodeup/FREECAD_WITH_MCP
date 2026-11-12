from bridge.client import call


def register(mcp):
    @mcp.tool()
    def freecad_boolean_union(document: str, name: str, base: str, tool: str) -> dict:
        """Une solidos, preservando referencias Base e Tool."""
        return call("boolean_union", locals())

    @mcp.tool()
    def freecad_boolean_cut(document: str, name: str, base: str, tool: str) -> dict:
        """Subtrai Tool de Base, preservando referencias parametricas."""
        return call("boolean_cut", locals())

    @mcp.tool()
    def freecad_boolean_intersection(document: str, name: str, base: str, tool: str) -> dict:
        """Calcula intersecao solida de Base e Tool."""
        return call("boolean_intersection", locals())
