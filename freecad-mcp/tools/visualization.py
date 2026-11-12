from bridge.client import call


def register(mcp):
    @mcp.tool()
    def freecad_fit_all(document: str) -> dict:
        """Enquadra todos os objetos na vista."""
        return call("fit_all", locals())

    @mcp.tool()
    def freecad_set_view(document: str, view: str) -> dict:
        """Seleciona isometric, front, rear, top, bottom, left ou right."""
        return call("set_view", locals())

    @mcp.tool()
    def freecad_capture_view(document: str, filename: str, width: int = 1200, height: int = 800, overwrite: bool = False) -> dict:
        """Captura vista GUI para PNG em modelos; dimensoes de 64 a 4096 pixels."""
        return call("capture_view", locals())
