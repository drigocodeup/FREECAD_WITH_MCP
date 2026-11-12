# Conjunto de engrenagens com caixa e tampa

Na barra **CESS — Geradores**, clique em **Conjunto de engrenagens**. A janela gera duas engrenagens externas de dentes retos, dois eixos paralelos e, opcionalmente, caixa e tampa com guia de centralização. Os seis objetos permanecem separados para exportação e têm um único objeto **Parametros** para recalcular o conjunto.

## Relação de redução ou aumento

O campo **Voltas entrada:saida** usa `X:Y`:

| Relação | Resultado | Dentes com o mínimo padrão |
|---|---|---|
| `2:1` | Entrada dá 2 voltas; saída dá 1 | 20 / 40 |
| `1:2` | Entrada dá 1 volta; saída dá 2 | 40 / 20 |
| `3:2` ou `1,5:1` | Redução de velocidade | 20 / 30 |
| `1:1` | Mesma velocidade, sentido oposto | 20 / 20 |

O número de dentes é calculado com inteiros para preservar exatamente a relação informada. **Minimo de dentes** é um limite inferior; o gerador pode aumentá-lo para compatibilizar a razão e evitar dentes abaixo do limiar conservador adotado para o ângulo de pressão. Há limite de 150 dentes por engrenagem. Uma relação que ultrapasse esse limite é rejeitada antes de criar objetos; múltiplas etapas não estão incluídas.

A janela mostra o tipo de transmissão, dentes de entrada/saída e distância entre eixos. Ambos usam o mesmo módulo e ângulo de pressão. A distância nominal é `modulo * (dentes_entrada + dentes_saida) / 2`; o campo **Acrescimo na distancia entre eixos** adiciona a folga configurada (padrão 0,1 mm). Esse acréscimo não é uma especificação de backlash. Combinações cuja razão de contato teórica não ultrapasse 1 são rejeitadas.

## Parâmetros da montagem

- Módulo, ângulo de pressão e espessura das engrenagens.
- Diâmetro e prolongamento dos dois eixos.
- Folga diametral entre furo e eixo.
- Acréscimo de distância entre eixos e posição angular da entrada. O perfil da saída recebe automaticamente a fase correspondente para engrenar.
- Parede/fundo/tampa, folga radial da caixa, folga axial e folga de passagem dos eixos.
- **Mostrar tampa separada**: ligado mostra a tampa ao lado; desligado coloca a tampa na posição montada. A guia tem 1 mm de profundidade/largura e 0,25 mm de folga lateral.

Após gerar, selecione **Parametros** na árvore e altere os campos na aba **Dados**. **InputTeeth**, **OutputTeeth**, **CenterDistance**, **ContactRatio**, **SpeedMultiplier** e **TransmissionMode** aparecem como resultados calculados. Alterar a relação ou módulo recalcula engrenagens, eixos, caixa e tampa em conjunto. Reabra o FCStd com a extensão CESS carregada para preservar essa edição.

## MCP e arquivos

Ferramenta compartilhada por STDIO e Streamable HTTP: `freecad_generate_gear_pair(document, name, ratio="2:1", ...)`.

Os exemplos em [`modelos/conjuntos_engrenagens`](../../modelos/conjuntos_engrenagens/) incluem FCStd, STEP, STL da montagem e STLs separados de cada componente. Exporte os objetos das peças, sem selecionar também o grupo ou o objeto Parametros.

## Validação e limites

O teste geométrico real usou relações 2:1, 1:2, 3:2 e 23:21 em quatro posições de entrada, com tampa montada. Verificou seis sólidos válidos e ausência de interseção volumétrica entre engrenagens, eixos, caixa e tampa nos pares pertinentes. Também editou relação/módulo e reabriu FCStd. A janela Qt foi testada com geração pelo botão e rejeição de relação inválida. Exemplos reais foram gerados por MCP STDIO e HTTP.

Relatórios: `gear-pair-geometry-validation.json`, `gear-pair-gui-validation.json` e `gear-pair-mcp-validation.json`, na pasta `freecad-mcp`.

O modelo usa eixos cilíndricos lisos e furos com folga. Chavetas, fixação das engrenagens nos eixos, rolamentos, parafusos de fechamento, lubrificação e cálculo de carga/vida não estão incluídos. A validação CAD não comprova ajuste de uma impressão física ou capacidade de transmitir torque. Os testes de movimento são amostras geométricas, não uma simulação dinâmica completa.

O tratamento conservador de poucos dentes segue o princípio de evitar undercut em perfis sem correção; veja a [referência técnica da KHK](https://khkgears.us/media/e5hdctid/gear-solutions_khk_addendum-modification-and-undercut.pdf). O perfil evolvente é criado pela biblioteca nativa `fcgear` do FreeCAD.
