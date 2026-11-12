from bridge.client import call


def register(mcp):
    @mcp.tool()
    def freecad_export_step(document: str, object_names: list[str], filename: str, overwrite: bool = False) -> dict:
        """Exporta objetos selecionados para .step em modelos."""
        return call("export_step", locals())

    @mcp.tool()
    def freecad_export_stl(document: str, object_names: list[str], filename: str, overwrite: bool = False) -> dict:
        """Exporta objetos selecionados para .stl em modelos, coordenadas em mm."""
        return call("export_stl", locals())

    @mcp.tool()
    def freecad_save_fcstd(document: str, filename: str, overwrite: bool = False) -> dict:
        """Salva projeto nativo FCStd em modelos."""
        return call("save_fcstd", locals())
