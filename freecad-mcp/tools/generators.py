from bridge.client import call


def register(mcp):
    @mcp.tool()
    def freecad_generate_gear(document: str, name: str, teeth: int = 24, module: float = 2,
                              pressure_angle: float = 20, thickness: float = 10, bore: float = 8) -> dict:
        """Gera engrenagem evolvente de dentes retos; modulo, espessura e furo em mm, angulo em graus. Parametros editaveis na arvore."""
        return call('generate_gear',locals())

    @mcp.tool()
    def freecad_generate_box_with_lid(document: str, name: str, length: float = 120, width: float = 80,
                                      height: float = 40, wall: float = 2, floor: float = 2,
                                      lid_thickness: float = 2, lip_depth: float = 5, clearance: float = .3) -> dict:
        """Gera caixa oca e tampa separada com guia de encaixe. Dimensoes externas da base e folga por lado em mm."""
        return call('generate_box_with_lid',locals())

    @mcp.tool()
    def freecad_generate_channel_letters(document: str, name: str, text: str = 'CESS', font_file: str = '',
                                         size: float = 60, depth: float = 20, wall: float = 1.5, floor: float = 2,
                                         spacing: float = 5, make_front: bool = True, front_thickness: float = 1.5,
                                         clearance: float = .2) -> dict:
        """Gera letras caixa ocas com fundo e frente plana separada opcional para colagem. Medidas em mm. Fonte TTF/OTF local; vazio usa a fonte padrao."""
        return call('generate_channel_letters',locals())

    @mcp.tool()
    def freecad_generate_channel_numbers(document: str, name: str, text: str = '123', font_file: str = '',
                                         size: float = 60, depth: float = 20, wall: float = 1.5, floor: float = 2,
                                         spacing: float = 5, make_front: bool = True, front_thickness: float = 1.5,
                                         clearance: float = .2) -> dict:
        """Gera numeros caixa ocos (digitos 0-9) com fundo e frente plana separada opcional. Medidas em mm; fonte vazia usa a padrao."""
        return call('generate_channel_numbers',locals())

    @mcp.tool()
    def freecad_generate_organizer(document: str, name: str, length: float = 120, width: float = 80,
                                   height: float = 40, wall: float = 2, floor: float = 2,
                                   rows: int = 2, columns: int = 3, divider: float = 2) -> dict:
        """Gera organizador aberto com compartimentos iguais em linhas/colunas; paredes, fundo e divisorias em mm."""
        return call('generate_organizer',locals())
