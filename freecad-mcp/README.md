# FreeCAD MCP — STDIO e Streamable HTTP

Novo: **CESS — Elétrica**, com biblioteca de comando, conexões, textos, prancha A0 a A4 e quadro inferior editável. [Guia](cess_gui/ELECTRICAL.md).

Novos: [Conjunto de engrenagens](cess_gui/GEAR_SETS.md), com dois eixos e caixa/tampa, e [Parafuso e porca](cess_gui/FASTENERS.md), com cabeça selecionável e rosca 3D real. São sete botões de geração e 43 ferramentas MCP.

O registro STDIO existente continua compatível. O modo HTTP usa o SDK oficial, autenticação obrigatória e validação de Host/Origin, mantendo o mesmo bridge gráfico e catálogo de 43 ferramentas. Veja [configuração dos transportes, Codex e ChatGPT Web](docs/TRANSPORTS.md), incluindo os limites da validação e os requisitos da conta para Secure MCP Tunnel.

Servidor MCP STDIO com 43 ferramentas que controlam o FreeCAD instalado. A geometria real e a GUI executam na thread principal Qt. O código-fonte original do FreeCAD foi preservado.

A inicialização carrega três barras: **CESS — Desenho**, com **Centralizar**, **Colocar cotas** e **Inserir texto**; **CESS — Geradores**, com sete geradores paramétricos; e **CESS — Elétrica**, para criar, editar e exportar diagramas com prancha. Consulte [desenho](cess_gui/README.md), [geradores](cess_gui/GENERATORS.md) e [elétrica](cess_gui/ELECTRICAL.md).

## Diagramas elétricos

Clique em **Nova prancha elétrica**, escolha A0 a A4, orientação, grade e dados do quadro inferior. Use a biblioteca para inserir os 17 símbolos disponíveis e **Fio (2 pontos)** para conectar terminais. Movimentação, rotação, textos e desfazer são integrados ao documento. Salve FCStd e exporte PDF/SVG/PNG/JSON em `modelos`.

O botão **Exemplo de comando** cria uma prancha de partida/parada com selo. [Exemplo FCStd](../modelos/eletrica/comando_contator.FCStd) · [PDF](../modelos/eletrica/comando_contator.pdf) · [Captura do editor](../modelos/eletrica/editor_exemplo.png).

São desenhos vetoriais próprios inspirados na organização do CADe_SIMU, sem importação `.cad` ou simulação elétrica. Os dois transportes compartilham as sete ferramentas `freecad_electrical_*`.

Na validação elétrica, os **29 testes passaram**, além dos testes gráficos e de todos os formatos. A execução selecionada teve **120 aprovados e 1 ignorado**. A regressão completa teve encerramento nativo do FreeCAD em `UIAutomationCore.dll` e **não foi aprovada**. Consulte [resultados, ocorrências e limites](docs/VALIDATION-ELECTRICAL.md).

## Ambiente instalado

- FreeCAD 1.1.1: `C:/Program Files/FreeCAD 1.1/bin/freecad.exe`.
- Python embarcado 3.11.14, 64 bits; nenhuma dependência instalada nele.
- Servidor: `.venv/Scripts/python.exe`, Python 3.12.10, 64 bits.
- SDK oficial `mcp==1.30.0`; linha 1.x fixada para compatibilidade FastMCP/ClientSession. Dependências exatas em `requirements-lock.txt`.
- Codex CLI `0.162.0-alpha.17.2`, servidor registrado como `freecad_local`.

## Iniciar

Na raiz `FreCAD_mcp`, execute:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\freecad-mcp\scripts\start.ps1
```

O script protege `.runtime` com ACL, gera a macro e inicia FreeCAD. Se o bridge já responde, reutiliza-o. Se uma instância FreeCAD já está aberta sem bridge, preserva a instância e informa a macro a executar por **Macro > Macros > Executar**: `freecad-mcp/.runtime/StartBridge.FCMacro`. Não injeta comandos em documentos abertos.

Para parar somente o bridge, mantendo FreeCAD e documentos:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\freecad-mcp\scripts\stop.ps1
```

Para reconectar após parada, execute a macro em uma nova sessão FreeCAD. O objeto de bridge permanece carregado na sessão antiga; não execute duas instâncias para a mesma pasta.

## Usar no Codex

Abra uma nova sessão Codex/VS Code depois do registro para atualizar o catálogo. Confira `codex mcp list` e `/mcp` no Codex CLI. Solicite:

> Use freecad_local para consultar freecad_health_check. Depois crie uma chapa de 100 × 60 × 5 mm com quatro furos de diâmetro 6 mm, com os centros a 10 mm das bordas. Valide um sólido e salve em modelos.

Sequência explícita de chamadas em `examples/placa_furada.json`. Os nomes retornados em `name`/`document` são identificadores internos; use-os em chamadas seguintes. As posições são absolutas; cilindros e cones crescem em +Z. Rotação define orientação absoluta no eixo informado, em graus. `copy_object` cria App::Link vinculado ao original. União pode conter mais de um sólido; inspecione `solids` se precisa de peça única.

Na raiz do repositorio, registre com o comando oficial e caminhos absolutos:

```powershell
$McpProject = (Resolve-Path .\freecad-mcp).Path
codex mcp add freecad_local -- "$McpProject\.venv\Scripts\python.exe" "$McpProject\server.py"
```

Os demais servidores foram preservados. Referência: [documentação oficial OpenAI sobre MCP](https://developers.openai.com/codex/mcp).

## Arquitetura e limites de segurança

`Codex → SDK MCP/STDIO → cliente TCP loopback autenticado → QTcpServer no FreeCAD → operações permitidas → Part/OCCT → modelos`.

- STDOUT contém somente MCP; logs do servidor vão para STDERR. O processo FreeCAD é separado, incluindo mensagens de exportação.
- Bridge escuta exclusivamente `127.0.0.1`, em porta dinâmica, com token aleatório renovado a cada inicialização. Endpoint e macro ficam em `.runtime`, protegida por ACL para o proprietário do projeto, usuário executor e SYSTEM. Não compartilhe essa pasta.
- Sem endpoints exec/eval, shell ou Python arbitrário. Operações e assinaturas são verificadas novamente no bridge.
- IDs UUID, prazo antes da execução, timeout de socket, limite de requisição de 64 KiB e cache de 128 respostas bem-sucedidas. Timeout não interrompe OCCT em execução: consulte o documento antes de repetir uma mutação.
- Arquivos abertos, salvos e exportados devem estar sob `../modelos`; caminhos são resolvidos antes da verificação, incluindo links. Arquivos existentes são rejeitados salvo `overwrite=true` explícito. Não use gravações concorrentes no mesmo destino.
- Primitivas e booleanas usam transações; booleanas mantêm Base/Tool e ocultam os operandos. Objetos com dependentes não podem ser excluídos.
- Salvar não grava automaticamente todos os documentos. Fechar documento modificado exige `discard=true`.
- Endpoint é local e confia nos usuários Windows autorizados a ler o token; não é um isolamento contra administrador ou código malicioso da mesma conta.

## Ferramentas

Prefixo comum `freecad_`:

| Grupo | Operações |
|---|---|
| Documentos | health_check, new_document, open_document, list_documents, save_document, close_document |
| Primitivas | create_box, create_cylinder, create_sphere, create_cone, create_torus |
| Booleanas | boolean_union, boolean_cut, boolean_intersection |
| Transformações | move_object, rotate_object, copy_object, delete_object |
| Inspeção | list_objects, get_object_properties, get_bounding_box, get_volume, validate_shape |
| Arquivos | export_step, export_stl, save_fcstd |
| GUI | fit_all, set_view, capture_view |
| Geradores | generate_gear, generate_box_with_lid, generate_channel_letters, generate_channel_numbers, generate_organizer |

Esquemas de entrada derivam das funções tipadas em `tools/`. Resultados são objetos JSON com validade, quantidade de sólidos, volume, limites ou caminhos, conforme a operação. Dimensões em mm, volumes em mm³; STL não armazena unidade, interprete as coordenadas como mm.

## Instalar novamente e testar

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\freecad-mcp\scripts\install.ps1
cd freecad-mcp
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest
$env:FREECAD_INTEGRATION='1'
.\.venv\Scripts\python.exe -m pytest -q --junitxml=test-results.xml
```

Execute pytest dentro de `freecad-mcp`, para não coletar os testes do código-fonte FreeCAD. Os testes de integração exigem o bridge real aberto; sem a variável são ignorados. Os testes não apagam nem sobrescrevem modelos: usam nomes exclusivos.

`integration-result.json` registra chamadas reais A–J, argumentos, resultados e volume após reabertura. `test-results.xml` registra o resultado da bateria. A peça principal é caixa 100 × 60 × 20 mm menos cilindro de raio 8 mm atravessando Z; volume teórico `120000 − π × 8² × 20 = 115978.76140340506 mm³`. O relatório indica o nome exato dos arquivos finais; execuções posteriores recebem sufixos para preservar os anteriores.

## Escopo e próximos incrementos

V1 validada para sólidos Part, FCStd, STEP, STL e captura PNG. Sketcher, PartDesign, Draft e TechDraw estão disponíveis na instalação, mas não há ferramentas V1 para esboços/restrições, páginas TechDraw cotadas, montagem, CAM ou G-code. STEP é geometria de entrada para um CAM, não um programa CNC pronto. A ativação das ferramentas no catálogo desta conversa não é retroativa; a execução real foi verificada por cliente oficial MCP STDIO e o registro do Codex foi conferido separadamente.
