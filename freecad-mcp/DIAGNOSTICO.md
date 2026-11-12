# Diagnóstico e entrega — 11/11/2026

## Inspeção inicial

- Workspace: `<workspace>`.
- Diretórios existentes: FreeCAD, CuraOpen, OrcaOpen. Nenhum servidor FreeCAD MCP foi encontrado no diretório destinado à integração; `freecad-mcp` foi criado sem modificar esses projetos.
- FreeCAD é checkout de fontes com `src`, `data`, `cMake`, `tests`, `tools`. Não foi compilado nem alterado.
- Nenhuma instância FreeCAD estava aberta no diagnóstico inicial. A instância utilizada nos testes foi iniciada para esta tarefa.
- Instalação executável encontrada em `C:/Program Files/FreeCAD 1.1/bin`: `freecad.exe`, `freecadcmd.exe`, `python.exe`, `FreeCAD.pyd`, `FreeCADApp.dll`, `FreeCADGui.pyd`, `python311.dll` e bibliotecas OCCT/Qt.
- Versão confirmada por `FreeCAD.Version()`: **1.1.1**, build 20260414, commit `0108fd4b4850cc46e625b60e53cea7a7bbe69f8d`.
- Python embarcado: **3.11.14**, conda-forge, AMD64/64 bits.
- Python do PATH: `<user-home>/AppData/Local/Programs/Python/Python312/python.exe`, **3.12.10**, AMD64/64 bits. `py -0p` não reconheceu instalações registradas; isso não impediu utilizar o executável localizado.
- Codex: `.../.vscode/extensions/openai.chatgpt-26.1007.21434-win32-x64/bin/windows-x86_64/codex.exe`, **0.162.0-alpha.17.2**.

## APIs examinadas

Fontes em `FreeCAD/src/Mod/{Part,PartDesign,Sketcher,Draft,TechDraw}`. As assinaturas de makeBox/makeCylinder estão em `Part/App/AppPartPy.cpp`. O estado Modified do documento gráfico foi conferido em `FreeCAD/src/Gui/DocumentPyImp.cpp`.

Importações reais com o Python embarcado, após `import FreeCAD`:

| API | Evidência e uso |
|---|---|
| Part | `Part.makeBox(1,2,3).Volume == 6.0`; sólidos e booleanas executados pela GUI nos testes MCP |
| Sketcher | importação bem-sucedida de `lib/Sketcher.pyd`; disponível para futuro Sketcher::SketchObject e restrições |
| PartDesign | importação de `Mod/PartDesign/__init__.py`; Body, Pad e Pocket fora do catálogo V1 |
| Draft | importação de `Mod/Draft/Draft.py`; construção 2D e operações Draft fora do catálogo V1 |
| TechDraw | importação de `lib/TechDraw.pyd`; páginas, vistas e cotas fora do catálogo V1 |

Não se assumiu importação FreeCAD pelo Python global. O processo MCP usa Python 3.12 em venv; o processo FreeCAD usa seu Python 3.11 e seus caminhos próprios. Um primeiro `import Part` isolado no Python embarcado falhou; inicializar `FreeCAD` antes de Part configurou os caminhos e permitiu o teste. Nenhuma DLL foi copiada entre versões.

## Arquitetura entregue

SDK oficial MCP Python 1.30.0/FastMCP via STDIO, cliente autenticado TCP loopback, servidor Qt QTcpServer dentro do FreeCAD e operações Part executadas na thread GUI. Sem exec/eval de entrada e sem endpoint público. Pastas autorizadas, limites, erros e timeouts documentados no README.

29 ferramentas em `tools/`; bridge e operações em `bridge/`; instalação/inicialização/parada/diagnóstico em `scripts/`; exemplo de quatro furos em `examples/placa_furada.json`. `server.py`, `config/settings.json`, `requirements.txt`, `requirements-lock.txt`, `pyproject.toml`, `AGENTS.md`, testes e documentação foram criados. `.runtime` contém credenciais locais e macro, não deve ser compartilhada.

## Dependências e problemas corrigidos

- Dependências instaladas somente em `freecad-mcp/.venv`; versões completas em `requirements-lock.txt`.
- SDK MCP 1.30.0, pytest 9.2.0 e dependências transitivas. `pip check`: **No broken requirements found**.
- A rede do sandbox bloqueou pip; download autorizado executado fora do sandbox.
- A instalação inicial encontrou falta de espaço. Cache pip de cerca de 816 MB foi removido com autorização; instalação foi concluída sem cache. Verificação posterior encontrou cerca de 13,4 GB livres.
- PowerShell bloqueava scripts pela política padrão; comandos usam `-ExecutionPolicy Bypass` somente no processo, sem alteração global.
- ACL inicial incluía somente a identidade sandbox; corrigida para incluir o proprietário real do projeto, permitindo FreeCAD e Codex do usuário acessarem o bridge.
- `App.Document.Modified` não existe nesta versão; corrigido para `Gui.Document.Modified`. Depois de salvar pelo App, o flag da GUI é sincronizado para permitir fechamento seguro.

## Resultados reais

Com bridge FreeCAD aberto e `FREECAD_INTEGRATION=1`, comando final:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --junitxml=test-results.xml
```

**14 passed, 1 skipped in 15.80s**. Único skip: criação de link simbólico Windows indisponível sem privilégio; demais testes de confinamento de caminhos passaram. Evidência: `test-results.xml`.

Teste A–J executado por cliente oficial MCP STDIO, incluindo inicialização MCP, chamadas de ferramentas, caixa 100 × 60 × 20 mm, cilindro Ø16 × 30 mm em (50,30,-5), subtração, validação de um sólido, FCStd, STEP, STL, fechamento, reabertura e consulta das referências Base/Tool. Evidência completa em `integration-result.json`.

- Volume teórico: **115978.76140340506 mm³**.
- Volume real após reabrir: **115978.76140340508 mm³**.
- Resultado: **válido, um sólido**, dependências Caixa e Cilindro preservadas.
- Arquivos da bateria final: `../modelos/TesteMCP_1794449378.FCStd`, `.step`, `.stl`, `.png`.
- Captura PNG inspecionada visualmente: placa com furo central visível.
- Reimportação independente dos arquivos exportados pelo Python embarcado: STEP válido, um sólido, volume 115978.76140340508 mm³; STL fechado com 520 facetas, volume aproximado 115980.4609375 mm³ (diferença de cerca de 0,00147% por triangulação). Evidência: `export-validation.json`.
- Verificações complementares exercitaram as demais primitivas, união (1500 mm³), interseção (500 mm³), rotação, cópia vinculada, translação, volume, limites, exclusão e save_document. Entradas negativas, tentativa de salvar fora de modelos, fechamento com alterações e exclusão de objeto com dependentes foram rejeitados.
- As execuções intermediárias foram preservadas em modelos. Os nomes recebem sufixos para não sobrescrever arquivos existentes.

## Status Codex e limites

Registro executado por `codex mcp add freecad_local -- <python absoluto> <server.py absoluto>`. `codex mcp get freecad_local` confirmou **enabled=true, transport=stdio**. `codex mcp list` confirmou freecad_local e preservou codex_app, cua_repl, node_repl, playwright e openaiDeveloperDocs com seus estados anteriores.

O teste MCP real ocorreu com cliente oficial SDK, não por uma ferramenta injetada retroativamente nesta conversa. Abra nova sessão Codex/VS Code para atualizar o catálogo. Instruções completas no README.

Sem falha pendente no fluxo Part/FCStd/STEP/STL testado. Ainda não implementados: ferramentas para desenhos TechDraw cotados, esboços Sketcher, operações PartDesign, CAM/G-code e gerenciamento de múltiplas instâncias. Uma operação OCCT em andamento não pode ser cancelada com segurança por timeout; consulte o estado antes de repetir. Nenhum teste comprova usinabilidade, tolerâncias de fabricação ou impressão física.
