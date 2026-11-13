# CESS — Elétrica

Editor de diagramas de comando elétrico integrado ao FreeCAD gráfico. Esta versão desenha e documenta; não executa simulação, cálculo elétrico ou verificação normativa.

## Criar um projeto

Inicie pelo script habitual `scripts/start.ps1`. Na barra **CESS - Eletrica**, clique **Nova prancha eletrica**. Escolha A0, A1, A2, A3 ou A4, paisagem/retrato, grade e dados do carimbo. A margem esquerda é 20 mm e as demais são 10 mm. O quadro inferior mede 180 × 35 mm; uma faixa inferior inteira é reservada para evitar sobreposição do desenho com o carimbo. Reduzir o papel exige que os elementos existentes caibam nos novos limites.

O carimbo permite editar empresa/escola, título, código do projeto, responsável, verificado, revisão, data e numeração das folhas. O botão **Prancha / carimbo** reabre essas opções; as propriedades também ficam no controlador do documento.

1. Escolha um símbolo na biblioteca e clique na prancha para inserir.
2. Use **Selecionar / mover** para arrastar na grade. O painel permite editar identificação, descrição, posição e rotação em passos de 90°.
3. Use **Fio (2 pontos)** e clique nos dois terminais. As ligações são ortogonais e acompanham os componentes. Pontos livres também são permitidos. Cruzamentos não criam junções automaticamente: use o símbolo de junção.
4. Insira textos, gire ou exclua elementos. Excluir um componente remove seus fios associados. **Desfazer** recupera a transação.
5. Salve o documento em FCStd e exporte a prancha para PDF, SVG, PNG ou JSON em `modelos`. O SVG/PDF exportado não inclui a grade do editor.

**Editar diagrama** abre a prancha selecionada ou permite escolher entre as existentes. **Exemplo de comando** cria um circuito desenhado de partida/parada com selo, 14 símbolos e 15 fios. As páginas são objetos TechDraw nativos e o FCStd conserva o SVG utilizado na prancha.

## Biblioteca inicial

A biblioteca inclui 77 símbolos vetoriais próprios, com 66 itens das barras de contatos do CADe_SIMU. Consulte o [inventário completo](../docs/CONTACTS-2D.md). Os tipos iniciais incluem: contato NA/NF, botoeira NA/NF, emergência, seletor, bobina, bobina temporizada, contato térmico NF, fusível, disjuntor, sinaleiro, motor, resistor, borne, junção e terra. Identificações podem se repetir entre bobina e contatos do mesmo dispositivo; IDs internos são únicos.

A pasta CADe_SIMU fornecida foi consultada como referência de organização funcional e identificação dos terminais. Não havia uma biblioteca SVG separada. Os desenhos foram implementados neste projeto: não foi incorporado o executável nem extraída sua biblioteca binária. Não há importação de arquivos `.cad` do CADe_SIMU nesta versão.

## MCP e limites

As sete ferramentas `freecad_electrical_*` são compartilhadas pelos servidores STDIO e HTTP: catálogo, criar, consultar, atualizar desenho, inserir símbolo, inserir fio e exportar. O catálogo total passa a 43 ferramentas. Coordenadas em mm partem do canto superior esquerdo da folha, com Y para baixo.

Para conectar, utilize os IDs retornados e os terminais do catálogo, por exemplo `{"symbol":"C1","pin":"14"}`. Também se aceita `{"point":[80,100]}`. A atualização completa recebe o objeto `drawing` retornado pela consulta; metadados e referências são validados antes da alteração. Não se aceita código executável ou SVG arbitrário de clientes.

Limites por prancha: 500 símbolos, 1.000 fios e 200 textos. O limite HTTP de corpo continua 64 KiB, portanto atualizações completas muito grandes podem ser rejeitadas antes do limite do modelo. O editor usa recursos do Qt e exige o FreeCAD gráfico. Carregar o FCStd para edição requer este módulo instalado. Impressão em papel e outros computadores/versões do FreeCAD ainda não foram testados.

## Testes

`FREECAD_INTEGRATION=1` habilita `tests/test_electrical_mcp.py`, que cria, altera, exporta e reabre documentos reais pelos dois transportes. `tests/freecad_electrical_gui.py` executa o teste do mouse e dos dez formatos no processo gráfico. Ao dispará-lo por macro `--single-instance`, agende `run(project)` com `QTimer.singleShot` para depois de a macro terminar: o cursor de espera do FreeCAD bloqueia eventos de entrada durante a execução direta da macro.

`tests/render_electrical_pdf.ps1` usa o leitor PDF do Windows para verificar e renderizar as páginas, sem dependências adicionais. A dimensão PDF pode ser arredondada para pontos pelo Qt; a verificação admite até 0,3 mm. Veja [evidências de validação](../docs/VALIDATION-ELECTRICAL.md).
