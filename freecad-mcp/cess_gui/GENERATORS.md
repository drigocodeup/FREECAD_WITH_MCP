# CESS — Geradores

Agora são **sete geradores; o catálogo atual inclui 43 ferramentas MCP com o módulo elétrico**. Os novos botões são **Conjunto de engrenagens**, com relação de redução/aumento e caixa com tampa, e **Parafuso e porca**, com cabeça Allen/sextavada e rosca helicoidal 3D real. Veja [conjuntos de engrenagens](GEAR_SETS.md) e [parafusos e porcas](FASTENERS.md). As seções abaixo registram os cinco geradores originais.

Cinco geradores paramétricos locais para o FreeCAD instalado. Não precisam compilar o FreeCAD, instalar complementos externos ou baixar fontes. Abra com `Iniciar_FreeCAD_CESS.cmd` para carregar as barras CESS e o bridge MCP.

## Usar e editar

Clique no botão do gerador, ajuste os campos e escolha **Gerar modelo**. Sem documento aberto, um documento é criado automaticamente. No documento existente, o resultado é adicionado em um grupo novo, sem substituir os objetos anteriores. Uma falha de validação permanece no diálogo e não cria o grupo.

Cada grupo contém **Parametros** e as peças geradas. Selecione Parametros na árvore e altere os valores na aba **Dados**; as peças vinculadas são recalculadas. Ctrl+Z desfaz a criação como uma transação. Os parâmetros são preservados em FCStd e continuam editáveis após reabrir.

Reabra os FCStd com a extensão carregada para que o Python encontre `cess_gui.generators`. As formas salvas podem continuar visíveis sem o módulo, mas a edição paramétrica depende dele. A fonte TTF/OTF usada nas letras também precisa estar disponível para recalcular.

## Os cinco botões

| Gerador | Parâmetros principais | Resultado |
|---|---|---|
| Engrenagem | Dentes (12–150), módulo, pressão (14,5–30°), espessura e diâmetro do furo | Engrenagem cilíndrica externa de dentes retos, perfil evolvente nativo do FreeCAD |
| Caixa com tampa | Comprimento, largura e altura externos da base, paredes, fundo, tampa, guia e folga por lado | Base oca e tampa separadas, lado a lado; tampa com guia interna de encaixe |
| Letra caixa | Letras, fonte, altura de maiúscula, profundidade, paredes, fundo, espaçamento e frente opcional | Corpos ocos abertos na frente e frentes planas separadas para colagem |
| Numeros caixa | Dígitos 0–9 e os mesmos parâmetros das letras | Corpos e frentes para números, incluindo zeros à esquerda |
| Organizador | Dimensões externas, paredes, fundo, linhas, colunas e divisórias | Bandeja aberta de compartimentos iguais; até 100 compartimentos |

As medidas são em mm; o ângulo é em graus. Furo zero gera engrenagem sem furo. A altura da caixa é a altura externa da base; a tampa acrescenta sua espessura ao conjunto fechado. No organizador, linhas distribuem compartimentos em Y e colunas em X.

A fonte padrão é Arial Bold instalada no Windows. Pode ser substituída por TTF/OTF local. Letras aceita letras e espaços; Numeros aceita dígitos ASCII e espaços, em uma linha de até 24 caracteres. Acentos e pontos podem gerar componentes físicos separados; há múltiplos sólidos por texto. Fontes muito finas ou contornos menores que a parede são rejeitados com uma mensagem, em vez de gerar uma casca defeituosa.

Os contornos externos dos corpos preservam as curvas da fonte. Para obter cavidades e frentes com exportação robusta, os contornos deslocados usam aproximação com desvio de corda de **0,03 mm**, seguida de offset e validação geométrica detalhada. A fonte não é distribuída no repositório.

## Encaixe e fabricação

- A caixa usa tampa com placa e guia, não dobradiça ou trava elástica. A folga é por lado, não diametral. Na posição montada da amostra, foi verificada ausência de interseção com a base.
- As frentes das letras/números são placas para colagem, com folga de contorno configurável. Não incluem presilhas, iluminação ou passagem de fios.
- A engrenagem é de dentes retos; não inclui helicoidal, cônica, cremalheira, chaveta ou análise de carga.
- O organizador tem divisórias fixas integradas ao fundo; não são divisórias removíveis.
- STEP preserva a geometria exata produzida; STL é triangulado e tem volume aproximado. O encaixe físico depende de material, processo e calibração e requer um corpo de prova.

Exporte as peças **Base/Tampa**, **Corpos/Frentes**, **Engrenagem** ou **Organizador**. Não selecione simultaneamente o grupo e seus filhos para exportar, pois isso pode duplicar geometria. Ao desligar MakeFront, o objeto Frentes permanece no grupo sem forma e volta a ser gerado quando a opção é ligada.

## Ferramentas MCP

O catálogo passa de 29 para **34 ferramentas**. Todos os geradores também podem ser acionados por linguagem natural:

- `freecad_generate_gear`
- `freecad_generate_box_with_lid`
- `freecad_generate_channel_letters`
- `freecad_generate_channel_numbers`
- `freecad_generate_organizer`

Todos recebem `document` e `name`. As demais opções correspondem aos campos do diálogo. O resultado informa o grupo, o objeto de parâmetros e os nomes das peças válidas para inspeção/exportação. Abra nova sessão do Codex após a atualização para recarregar o catálogo.

Exemplo: “Crie um documento e use freecad_generate_box_with_lid para uma caixa 120 × 80 × 40 mm, parede e fundo de 2 mm, guia de 5 mm e folga de 0,3 mm por lado. Salve e exporte as duas peças.”

## Evidências e reprodução

- `tests/test_generator_specs.py`: validação de limites, tipos, conteúdo e combinações incompatíveis.
- `tests/freecad_generators_geometry.py`: executa com o Python embarcado do FreeCAD; verifica volumes, cavidades, montagem da tampa, compartimentos, alfabeto A–Z, ÇÁ, dígitos 0–9, exportação/reimportação, edição paramétrica e recuperação de parâmetro inválido.
- O modo `reload` do mesmo script reabre os FCStd em outro processo e altera os parâmetros, comprovando que a edição não depende de estado em memória do processo anterior.
- `tests/freecad_generators_gui.py`: smoke test dentro da GUI real; aciona o botão Qt de cada diálogo, gera os cinco modelos, exporta e captura vistas.
- `tests/test_generators_mcp.py`: inicializa cliente oficial MCP STDIO, chama os cinco geradores e rejeita uma entrada inválida sem criar objetos.

Relatórios: `../generators-geometry-validation.json`, `../generators-gui-validation.json`, `../generators-export-validation.json`, `../generators-mcp-validation.json` e `../generators-test-results.xml`. Os exemplos finais estão em `../../modelos/geradores/`; os FCStd usados na persistência estão em `../../modelos/geradores_parametricos/`.

Para repetir a geometria (substitua o executável pela sua instalação):

```powershell
cd freecad-mcp
& 'C:\Program Files\FreeCAD 1.1\bin\python.exe' -u tests/freecad_generators_geometry.py
& 'C:\Program Files\FreeCAD 1.1\bin\python.exe' -u tests/freecad_generators_geometry.py reload generators-geometry-validation.json
```

Os scripts gráficos precisam ser executados por uma macro confiável na thread Qt do FreeCAD. O pytest comum não simula uma GUI nem valida usinagem ou impressão física.
