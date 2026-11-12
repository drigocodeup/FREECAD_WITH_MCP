# FreeCAD with MCP

Integração local para controlar o FreeCAD por linguagem natural usando Codex e o protocolo MCP. V1 para Windows, com 29 ferramentas para documentos, sólidos, booleanas, transformações, inspeção, exportação e captura da vista.

![Peça criada por chamadas MCP reais](modelos/TesteMCP_1794449378.png)

## Requisitos

- Windows com FreeCAD instalado; validado com FreeCAD 1.1.1 de 64 bits.
- Python 3.11 ou superior para o servidor; validado com Python 3.12.10.
- Codex CLI/VS Code para usar o servidor como ferramentas do assistente.

Não é necessário clonar ou compilar o código-fonte do FreeCAD. O servidor roda em ambiente virtual separado do Python embarcado do FreeCAD.

## Instalação

```powershell
git clone https://github.com/drigocodeup/FREECAD_WITH_MCP.git
cd FREECAD_WITH_MCP
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\freecad-mcp\scripts\install.ps1
```

Confira o caminho do FreeCAD em `freecad-mcp/config/settings.json`; o padrão é `C:/Program Files/FreeCAD 1.1/bin/freecad.exe`.

Inicie o bridge:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\freecad-mcp\scripts\start.ps1
```

Se FreeCAD já estiver aberto, o script informa a macro a executar pelo menu **Macro > Macros**, preservando a instância existente.

Registre o servidor com os caminhos absolutos da sua cópia:

```powershell
$McpProject = (Resolve-Path .\freecad-mcp).Path
codex mcp add freecad_local -- "$McpProject\.venv\Scripts\python.exe" "$McpProject\server.py"
codex mcp list
```

Abra uma nova sessão Codex para atualizar o catálogo e solicite:

> Use freecad_local para consultar o estado do FreeCAD. Crie uma caixa de 100 × 60 × 20 mm com furo passante central de diâmetro 16 mm. Valide um sólido e salve FCStd, STEP e STL na pasta modelos.

## Arquitetura

`Codex → MCP STDIO → bridge local autenticado → thread principal Qt do FreeCAD → Part/OCCT → arquivos`.

O bridge aceita somente operações permitidas, sem execução arbitrária de Python. Escuta exclusivamente em loopback; o token fica em `.runtime`, protegida por ACL no Windows e excluída do Git. Gravações são restritas à pasta `modelos`, sem sobrescrita por padrão.

## Validação

Na execução local registrada: **14 testes aprovados e 1 ignorado** por privilégio Windows de link simbólico. A integração foi testada com chamadas MCP reais, incluindo salvar, fechar e reabrir a peça.

- Volume teórico: **115978,76140340506 mm³**.
- Volume medido após reabrir: **115978,76140340508 mm³**.
- STEP reimportado: um sólido válido.
- STL reimportado: malha fechada com 520 facetas; volume aproximado por triangulação.

Arquivos demonstrativos em [modelos](modelos). Evidências: [relatório de integração](freecad-mcp/integration-result.json), [validação das exportações](freecad-mcp/export-validation.json) e [resultado dos testes](freecad-mcp/test-results.xml). Caminhos locais foram substituídos por marcadores para publicação.

Para executar os testes:

```powershell
cd freecad-mcp
.\.venv\Scripts\python.exe -m pytest
# Com o bridge real aberto:
$env:FREECAD_INTEGRATION='1'
.\.venv\Scripts\python.exe -m pytest -q
```

Os testes de integração criam arquivos locais novos. Não exigem nem enviam dados para serviços de IA; o transporte entre MCP e FreeCAD é local.

## Escopo e evolução

V1 implementa sólidos Part, FCStd, STEP, STL e PNG. Desenhos TechDraw cotados, ferramentas de esboço, CAM/G-code e os botões da próxima etapa ainda não estão implementados.

Consulte [instruções detalhadas](freecad-mcp/README.md), [diagnóstico da execução](freecad-mcp/DIAGNOSTICO.md) e [próximas melhorias](ROADMAP.md).
