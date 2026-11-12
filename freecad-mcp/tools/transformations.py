from bridge.client import call


def register(mcp):
    @mcp.tool()
    def freecad_move_object(document: str, object_name: str, position: list[float]) -> dict:
        """Define posicao absoluta XYZ em mm; preserva rotacao."""
        return call("move_object", locals())

    @mcp.tool()
    def freecad_rotate_object(document: str, object_name: str, axis: list[float], angle: float) -> dict:
        """Define rotacao absoluta no eixo XYZ, angulo em graus; preserva translacao."""
        return call("rotate_object", locals())

    @mcp.tool()
    def freecad_copy_object(document: str, object_name: str, name: str) -> dict:
        """Cria copia vinculada App::Link preservando referencia ao original."""
        return call("copy_object", locals())

    @mcp.tool()
    def freecad_delete_object(document: str, object_name: str) -> dict:
        """Remove objeto somente se nao possui dependentes."""
        return call("delete_object", locals())
