from bridge.client import call


def register(mcp):
    @mcp.tool()
    def freecad_electrical_catalog() -> dict:
        """Lista simbolos vetoriais, categorias e terminais do modulo de desenho eletrico, sem simulacao."""
        return call('electrical_catalog')

    @mcp.tool()
    def freecad_electrical_create_sheet(document: str,name: str,paper: str='A3',orientation: str='landscape',
                                        title: str='Projeto eletrico',company: str='',project: str='',author: str='') -> dict:
        """Cria prancha eletrica TechDraw A0-A4 com margens e quadro inferior editavel. Coordenadas em mm a partir do canto superior esquerdo."""
        return call('electrical_create_sheet',locals())

    @mcp.tool()
    def freecad_electrical_get_sheet(document: str,sheet: str) -> dict:
        """Valida e consulta desenho, carimbo, limites uteis e IDs de simbolos/fios da prancha eletrica."""
        return call('electrical_get_sheet',locals())

    @mcp.tool()
    def freecad_electrical_update_sheet(document: str,sheet: str,drawing: dict) -> dict:
        """Substitui desenho eletrico validado; preserva a prancha se houver referencias invalidas ou itens fora das margens. Sem codigo executavel."""
        return call('electrical_update_sheet',locals())

    @mcp.tool()
    def freecad_electrical_add_symbol(document: str,sheet: str,kind: str,x: float,y: float,
                                      tag: str='',rotation: float=0,description: str='') -> dict:
        """Insere simbolo do catalogo; posicao em mm, rotacao multipla de 90 graus. Retorna ID para conectar terminais."""
        return call('electrical_add_symbol',locals())

    @mcp.tool()
    def freecad_electrical_add_wire(document: str,sheet: str,start: dict,end: dict,label: str='',
                                    waypoints: list[list[float]]=[],color: str='#111111') -> dict:
        """Desenha fio ortogonal entre {symbol:ID,pin:terminal} ou {point:[x,y]}. Terminais acompanham movimentacao. Cruzamento nao cria juncao automaticamente."""
        return call('electrical_add_wire',locals())

    @mcp.tool()
    def freecad_electrical_export_sheet(document: str,sheet: str,filename: str,overwrite: bool=False) -> dict:
        """Exporta prancha para PDF no tamanho real do papel, SVG vetorial, PNG ou JSON, somente em modelos."""
        return call('electrical_export_sheet',locals(),timeout=60)
