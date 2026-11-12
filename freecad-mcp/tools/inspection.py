from bridge.client import call


def register(mcp):
    @mcp.tool()
    def freecad_list_objects(document: str) -> dict:
        """Lista objetos e dependencias."""
        return call("list_objects", locals())

    @mcp.tool()
    def freecad_get_object_properties(document: str, object_name: str) -> dict:
        """Consulta propriedades e geometria."""
        return call("get_object_properties", locals())

    @mcp.tool()
    def freecad_get_bounding_box(document: str, object_name: str) -> dict:
        """Consulta limites XYZ e dimensoes em mm."""
        return call("get_bounding_box", locals())

    @mcp.tool()
    def freecad_get_volume(document: str, object_name: str) -> dict:
        """Consulta volume em mm cubicos."""
        return call("get_volume", locals())

    @mcp.tool()
    def freecad_validate_shape(document: str, object_name: str) -> dict:
        """Recalcula e verifica validade, quantidade de solidos e volume."""
        return call("validate_shape", locals())
