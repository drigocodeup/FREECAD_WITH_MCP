from bridge.client import call


def register(mcp):
    @mcp.tool()
    def freecad_health_check() -> dict:
        """Consulta versao, GUI, documentos e disponibilidade do bridge."""
        return call("health_check", locals())

    @mcp.tool()
    def freecad_new_document(name: str) -> dict:
        """Cria documento vazio com nome exclusivo."""
        return call("new_document", locals())

    @mcp.tool()
    def freecad_open_document(filename: str) -> dict:
        """Abre FCStd dentro da pasta modelos."""
        return call("open_document", locals())

    @mcp.tool()
    def freecad_list_documents() -> dict:
        """Lista documentos abertos."""
        return call("list_documents", locals())

    @mcp.tool()
    def freecad_save_document(document: str, filename: str, overwrite: bool = False) -> dict:
        """Salva documento FCStd em modelos; nao sobrescreve por padrao."""
        return call("save_document", locals())

    @mcp.tool()
    def freecad_close_document(document: str, discard: bool = False) -> dict:
        """Fecha documento; exige descarte explicito se modificado."""
        return call("close_document", locals())
