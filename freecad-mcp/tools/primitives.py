from bridge.client import call


def register(mcp):
    @mcp.tool()
    def freecad_create_box(document: str, name: str, length: float, width: float, height: float, position: list[float] = [0, 0, 0]) -> dict:
        """Cria caixa parametrica; dimensoes positivas em mm e posicao absoluta XYZ."""
        return call("create_box", locals())

    @mcp.tool()
    def freecad_create_cylinder(document: str, name: str, radius: float, height: float, position: list[float] = [0, 0, 0]) -> dict:
        """Cria cilindro parametrico ao longo de Z; raio e altura em mm."""
        return call("create_cylinder", locals())

    @mcp.tool()
    def freecad_create_sphere(document: str, name: str, radius: float, position: list[float] = [0, 0, 0]) -> dict:
        """Cria esfera parametrica; raio em mm."""
        return call("create_sphere", locals())

    @mcp.tool()
    def freecad_create_cone(document: str, name: str, radius1: float, radius2: float, height: float, position: list[float] = [0, 0, 0]) -> dict:
        """Cria cone ao longo de Z; permite um raio zero; medidas em mm."""
        return call("create_cone", locals())

    @mcp.tool()
    def freecad_create_torus(document: str, name: str, radius1: float, radius2: float, position: list[float] = [0, 0, 0]) -> dict:
        """Cria toro parametrico; raio maior deve exceder raio do tubo, em mm."""
        return call("create_torus", locals())
