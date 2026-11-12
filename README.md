# FreeCAD with MCP

Novo módulo **CESS — Elétrica**: diagramas com 17 símbolos de comando, fios, textos e prancha A0 a A4 com carimbo editável. [Como usar](freecad-mcp/cess_gui/ELECTRICAL.md) · [Exemplo FCStd](modelos/eletrica/comando_contator.FCStd) · [Prancha PDF](modelos/eletrica/comando_contator.pdf). Somente desenho, sem simulação.

Novos geradores: [conjunto de engrenagens com dois eixos, caixa e tampa](freecad-mcp/cess_gui/GEAR_SETS.md), configurado por relação entrada:saída, e [parafuso/porca com cabeça Allen ou sextavada e rosca 3D real](freecad-mcp/cess_gui/FASTENERS.md). Ambos têm janela de parâmetros e ferramentas MCP nos dois transportes.

Dois transportes compartilham as mesmas 43 ferramentas: **STDIO** para Codex/VS Code e **Streamable HTTP autenticado** para clientes remotos. O HTTP usa localhost por padrão; a preparação para ChatGPT Web inclui OAuth externo e Secure MCP Tunnel, sem publicação automática. Consulte [instalação, segurança e integração com ChatGPT](freecad-mcp/docs/TRANSPORTS.md).

Integração local para controlar o FreeCAD por linguagem natural usando Codex e o protocolo MCP. Para Windows, com 43 ferramentas para documentos, sólidos, booleanas, transformações, inspeção, geradores, exportação e captura da vista.

Inclui também a barra **CESS — Desenho**, com os botões **Centralizar**, **Colocar cotas** e **Inserir texto**. [Como usar a barra](freecad-mcp/cess_gui/README.md).

A barra **CESS — Geradores** oferece sete geradores: **Engrenagem**, **Conjunto de engrenagens**, **Parafuso e porca**, **Caixa com tampa**, **Letra caixa**, **Números caixa** e **Organizador**, com diálogos e parâmetros editáveis no documento. [Instruções dos geradores](freecad-mcp/cess_gui/GENERATORS.md).

## Diagramas elétricos

Na barra **CESS — Elétrica**, use **Nova prancha elétrica**, **Editar diagrama**, **Exportar prancha** ou **Exemplo de comando**.

- Escolha papel **A0, A1, A2, A3 ou A4**, em retrato ou paisagem.
- Margem esquerda de 20 mm, demais de 10 mm e quadro inferior de 180 × 35 mm, com espaço reservado para o carimbo.
- Edite empresa/escola, título, código do projeto, responsável, verificação, revisão, data e numeração das folhas.
- Insira contatos NA/NF, botoeiras, bobinas, proteções, sinaleiro, motor, bornes e outros símbolos; são **17 símbolos vetoriais**.
- Desenhe fios ortogonais entre terminais, mova componentes, gire, insira textos e desfaça alterações. Os fios acompanham os componentes.
- Salve em **FCStd** com página TechDraw e exporte **PDF, SVG, PNG ou JSON** para `modelos`.

![Editor elétrico com comando de partida, parada e selo](modelos/eletrica/editor_exemplo.png)

[Abrir exemplo FCStd](modelos/eletrica/comando_contator.FCStd) · [Prancha PDF](modelos/eletrica/comando_contator.pdf) · [Imagem da prancha](modelos/eletrica/comando_contator.png) · [Manual do módulo](freecad-mcp/cess_gui/ELECTRICAL.md)

A organização funcional foi inspirada nas referências locais do CADe_SIMU. Os símbolos são próprios; esta versão não importa arquivos `.cad`, não simula circuitos e não realiza verificação normativa.

## Exemplos mecânicos

| Gerador | Exemplo FCStd | Prévia |
|---|---|---|
| Conjunto com caixa e tampa | [Redução 2:1](modelos/conjuntos_engrenagens/reducao_2_1.FCStd) | [Imagem](modelos/conjuntos_engrenagens/reducao_2_1.png) |
| Parafuso Allen e porca | [Abrir modelo](modelos/parafusos_porcas/allen.FCStd) | [Imagem](modelos/parafusos_porcas/allen.png) |
| Engrenagem evolvente | [Abrir modelo](modelos/geradores/gear.FCStd) | [Imagem](modelos/geradores/gear.png) |
| Caixa com tampa e guia | [Abrir modelo](modelos/geradores/box.FCStd) | [Imagem](modelos/geradores/box.png) |
| Letras caixa ocas | [Abrir modelo](modelos/geradores/letters.FCStd) | [Imagem](modelos/geradores/letters.png) |
| Números caixa ocos | [Abrir modelo](modelos/geradores/numbers.FCStd) | [Imagem](modelos/geradores/numbers.png) |
| Organizador com divisórias | [Abrir modelo](modelos/geradores/organizer.FCStd) | [Imagem](modelos/geradores/organizer.png) |

Cada exemplo também tem STEP e STL na mesma pasta.

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

Também é possível abrir com `Iniciar_FreeCAD_CESS.cmd`. O lançador carrega as barras de desenho, geradores e elétrica na aplicação instalada, sem compilar as fontes do FreeCAD.

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

`Cliente → MCP STDIO ou Streamable HTTP → bridge local autenticado → thread principal Qt do FreeCAD → Part/OCCT ou TechDraw → arquivos`.

O bridge aceita somente operações permitidas, sem execução arbitrária de Python. Escuta exclusivamente em loopback; o token fica em `.runtime`, protegida por ACL no Windows e excluída do Git. Gravações são restritas à pasta `modelos`, sem sobrescrita por padrão.

## Validação

Validação mais recente do módulo elétrico, em **12/11/2026**:

- **29 testes elétricos aprovados**, incluindo criação, edição, exportação e reabertura de documentos reais pelos dois transportes MCP.
- Teste gráfico com inserção de símbolos e fio por mouse, edição de posição, atualização das conexões, desfazer e edição do carimbo.
- Dez combinações de formato/orientação verificadas em TechDraw e nos PDFs exportados; exemplo FCStd reaberto e PDF revisado visualmente.
- **120 testes aprovados e 1 ignorado** na execução selecionada, excluindo os testes MCP de conjuntos de engrenagens e dos cinco geradores.

**Limitação da regressão completa:** a aplicação FreeCAD encerrou durante os geradores mecânicos. A última execução completa terminou com **118 aprovados, 4 falhas e 1 ignorado**; as chamadas posteriores falharam porque o bridge foi perdido. Os registros nativos apontaram `UIAutomationCore.dll`, sem causa raiz determinada. A regressão completa não está aprovada. Impressão física e outros computadores/versões do FreeCAD ainda não foram testados.

[Relatório elétrico e limites](freecad-mcp/docs/VALIDATION-ELECTRICAL.md) · [Resumo da regressão](freecad-mcp/electrical-regression-summary.json) · [Interface gráfica](freecad-mcp/electrical-gui-validation.json) · [STDIO](freecad-mcp/electrical-stdio-validation.json) · [HTTP](freecad-mcp/electrical-http-validation.json) · [PDFs](freecad-mcp/electrical-pdf-validation.json)

Resultados anteriores, preservados como histórico da implementação:

A primeira integração mecânica teve **14 testes aprovados e 1 ignorado** por privilégio Windows de link simbólico, incluindo salvar, fechar e reabrir a peça:

- Volume teórico: **115978,76140340506 mm³**.
- Volume medido após reabrir: **115978,76140340508 mm³**.
- STEP reimportado: um sólido válido.
- STL reimportado: malha fechada com 520 facetas; volume aproximado por triangulação.

Arquivos demonstrativos em [modelos](modelos). Evidências: [relatório de integração](freecad-mcp/integration-result.json), [validação das exportações](freecad-mcp/export-validation.json) e [resultado dos testes](freecad-mcp/test-results.xml). Caminhos locais foram substituídos por marcadores para publicação.

A extensão de desenho tem validação adicional: **17 testes aprovados e 3 ignorados** na bateria comum (integração CAD desligada e privilégio de link simbólico ausente), mais smoke test em uma instância gráfica real. O smoke test verificou centralização, desfazer/refazer, cota de 100 mm, texto e os comandos interativos. [Evidência da GUI](freecad-mcp/gui-validation.json).

Na bateria completa após adicionar os geradores: **47 testes aprovados e 1 ignorado**, incluindo chamadas MCP reais aos cinco geradores. Os testes gráficos, geométricos e de persistência também passaram. As exportações dos cinco modelos foram reimportadas: STEP com todos os sólidos preservados e STL com malhas fechadas. [Resultado pytest](freecad-mcp/generators-test-results.xml) · [Geometria e persistência](freecad-mcp/generators-geometry-validation.json) · [GUI](freecad-mcp/generators-gui-validation.json) · [Exportações](freecad-mcp/generators-export-validation.json) · [MCP](freecad-mcp/generators-mcp-validation.json).

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

O projeto implementa sólidos Part, sete geradores paramétricos, centralização entre objetos independentes, cotas/textos Draft e diagramas elétricos em páginas TechDraw. Exporta modelos mecânicos em FCStd/STEP/STL/PNG e pranchas elétricas em PDF/SVG/PNG/JSON. Desenhos mecânicos TechDraw cotados, centralização dentro do mesmo esboço, simulação elétrica e CAM/G-code ainda não estão implementados.

Consulte [instruções detalhadas](freecad-mcp/README.md), [diagnóstico da execução](freecad-mcp/DIAGNOSTICO.md) e [próximas melhorias](ROADMAP.md).
