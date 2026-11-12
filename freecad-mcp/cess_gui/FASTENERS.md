# Parafuso e porca com rosca 3D real

Na barra **CESS — Geradores**, clique em **Parafuso e porca**. Selecione **allen** ou **sextavada**, ajuste os parâmetros e pressione **Gerar modelo**.

São criados dois sólidos separados, **Parafuso** e **Porca**, com rosca helicoidal geométrica real de 60°. A rosca permanece no STEP e no STL; não é textura nem empilhamento de anéis. A porca é gerada com um perfil correspondente ao parafuso e folga ajustável. Os dois compartilham um objeto **Parametros** editável na árvore.

## Campos

| Campo | Uso |
|---|---|
| Tipo de cabeça | Allen cilíndrica com encaixe hexagonal interno, ou sextavada externa |
| Diâmetro nominal | Diâmetro externo da rosca, em mm |
| Passo | Avanço axial por volta, em mm |
| Comprimento sob a cabeça | Comprimento da haste totalmente roscada; a cabeça acrescenta sua altura |
| Tamanho da cabeça | Diâmetro externo na Allen; medida entre faces na sextavada |
| Altura da cabeça | Configurável para os dois tipos |
| Chave e profundidade Allen | Encaixe interno; ficam desabilitados na cabeça sextavada |
| Chave da porca | Distância entre faces opostas do hexágono externo |
| Altura da porca | Comprimento axial da rosca interna |
| Folga diametral | Aumenta o perfil interno da porca em relação ao parafuso; 0,3 mm por padrão |
| Rosca esquerda | Desmarcada gera rosca direita; marcada inverte a hélice de ambas as peças |

Exemplo inicial: diâmetro 8 mm, passo 1,25 mm, haste 30 mm, cabeça Allen Ø13 × 8 mm, chave 6 mm com 4 mm de profundidade e porca de chave 13 × 6,5 mm. Todas as dimensões podem ser alteradas; mudar o diâmetro não seleciona automaticamente uma tabela comercial de cabeças.

Para limitar custo e falhas de booleanas, cada peça admite até 40 voltas de rosca real. O gerador valida combinações de passo/diâmetro, parede da porca, profundidade do encaixe Allen e tamanho da cabeça antes de alterar o documento. Uma entrada inválida mostra mensagem e não cria o conjunto.

## Exportação e MCP

Selecione **Parafuso** ou **Porca** e exporte individualmente para STL. Para manter a edição, salve FCStd e reabra com a extensão CESS carregada. STEP preserva a geometria do par. Os exemplos ficam em [`modelos/parafusos_porcas`](../../modelos/parafusos_porcas/).

Ferramenta disponível nos dois transportes: `freecad_generate_fastener(document, name, head_type="allen", diameter=8, pitch=1.25, ...)`.

## O que foi verificado

Os testes reais do kernel verificam cabeça Allen/sextavada, rosca direita/esquerda, um sólido válido por peça, malhas fechadas, volume aproximado do STL e reimportação STEP. A porca foi posicionada virtualmente no parafuso em quatro posições de avanço/rotação, sem interseção volumétrica. Há também testes da janela Qt, edição paramétrica/reabertura FCStd e criação/exportação por MCP STDIO e HTTP.

Relatórios: `fastener-geometry-validation.json`, `fastener-gui-validation.json` e `fastener-mcp-validation.json` em `freecad-mcp`.

O perfil usa raízes e cristas truncadas para protótipos; não declara conformidade dimensional com classe de tolerância ISO, resistência mecânica ou intercâmbio com porcas comerciais. Encaixe físico depende do material e da calibração da impressora e ainda não foi testado. A folga é configurável para permitir essa calibração.

A construção segue operações nativas Part/OCCT com hélice segmentada, varredura e booleanas. A separação entre início da hélice e costura do cilindro evita uma das falhas descritas no [tutorial oficial de roscas do FreeCAD](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Thread_for_Screw_Tutorial.md). Não exige instalar um workbench externo.
