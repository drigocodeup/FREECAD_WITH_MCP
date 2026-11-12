# Validação dos novos geradores mecânicos

Implementação verificada no Windows com FreeCAD 1.1.1, Python embarcado 3.11.14 e SDK MCP 1.30.0. Os botões foram carregados na instância gráfica existente por uma macro local confiável, usando a opção nativa `--single-instance`; os documentos anteriores foram preservados. Não foi criado endpoint de execução arbitrária.

## Resultados

- **93 testes pytest aprovados e 1 ignorado** com `FREECAD_INTEGRATION=1`. O teste ignorado exige privilégio Windows para symlink. Há um aviso de depreciação de TestClient/httpx, sem falha.
- Catálogo compartilhado de **36 ferramentas** conferido por clientes MCP STDIO e HTTP TCP reais; autenticação e validação de Host/Origin continuam testadas.
- Janelas Qt dos dois geradores testadas pelo sinal do botão real: seleção, campos, geração válida e rejeição de parâmetros inválidos sem objetos parciais.
- FCStd salvo, fechado e reaberto pelo MCP nos quatro exemplos (redução, aumento, Allen e sextavada).
- `pip check` sem dependências quebradas. Nenhuma dependência adicional ou workbench externo instalado.

Relatório: [mechanical-generators-test-results.xml](../mechanical-generators-test-results.xml).

## Engrenagens

[Geometria real](../gear-pair-geometry-validation.json): relações 2:1, 1:2, 3:2 e 23:21, em quatro posições angulares cada. Seis sólidos válidos, com tampa montada e sem interseção volumétrica nos pares de peças verificados. Edição de módulo/relação e reabertura paramétrica também passaram.

[Janela Qt](../gear-pair-gui-validation.json) e [chamadas MCP](../gear-pair-mcp-validation.json): redução 2:1 por STDIO e aumento 1:2 por HTTP, com exportação da montagem e STLs por componente.

Exemplos: [redução 2:1](../../modelos/conjuntos_engrenagens/reducao_2_1.FCStd), [aumento 1:2](../../modelos/conjuntos_engrenagens/aumento_1_2.FCStd). Ambos usam módulo 2, 20/40 ou 40/20 dentes, distância nominal 60 mm e acréscimo de 0,1 mm entre eixos.

## Parafuso e porca

[Geometria real](../fastener-geometry-validation.json): cabeças Allen e sextavada, roscas direita e esquerda. Um sólido válido por peça, verificação OCCT detalhada, malhas fechadas com volume dentro de 2% do CAD e STEP reimportado com dois sólidos e volume correspondente. Encaixe virtual em quatro posições de avanço/rotação sem interseção volumétrica. Edição de cabeça/comprimento/sentido e reabertura FCStd passaram.

[Parâmetros alternativos](../fastener-parameters-validation.json): diâmetro 6 mm, passo 1 mm, comprimento 20 mm, cabeça 10 × 6 mm e porca chave 10 × 5 mm, com folga diametral 0,25 mm. Sólidos verificados e encaixe virtual sem interseção.

[Janela Qt](../fastener-gui-validation.json) e [chamadas MCP](../fastener-mcp-validation.json): Allen por STDIO e sextavada por HTTP, com STEP e STL individual de cada peça.

Exemplos: [Allen](../../modelos/parafusos_porcas/allen.FCStd) e [sextavada](../../modelos/parafusos_porcas/sextavada.FCStd), ambos com diâmetro 8 mm, passo 1,25 mm e comprimento sob a cabeça de 30 mm.

## Falhas encontradas e correções

A primeira hélice contínua produziu geometria inválida. A construção foi corrigida com hélice segmentada e separação entre início da hélice e costura do cilindro; a validação passou nos dois sentidos e cabeças. Um teste de persistência tentou ler `LastError` de um grupo; o filtro do teste foi corrigido e a execução completa repetida com sucesso.

Uma execução sob carga simultânea encontrou `httpx.ReadTimeout` (prazo padrão de 5 s no cliente) e timeout de 30 s em um gerador existente. Os documentos afetados foram inspecionados antes de novas tentativas. Os clientes de integração CAD agora aguardam até 120 s e chamadas de geradores ao bridge têm prazo de 90 s, dentro do limite de 120 s já imposto pelo bridge. A execução final foi feita sem concorrência com os testes CAD de outro processo e passou integralmente.

Os modelos são protótipos CAD: impressão e encaixe físicos, resistência do parafuso e transmissão de torque do conjunto não foram ensaiados. Consulte as limitações em [engrenagens](../cess_gui/GEAR_SETS.md) e [parafusos](../cess_gui/FASTENERS.md).
