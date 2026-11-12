# Evidências da validação local — 12/11/2026

Ambiente: Windows, Python do servidor 3.12.10, SDK oficial MCP 1.30.0, FreeCAD instalado 1.1.1 com GUI e operações na thread principal Qt. Nenhuma dependência foi instalada no Python embarcado.

## Resultados confirmados

- STDIO: inicialização MCP, catálogo de 34 ferramentas, validação de parâmetros e modelagem real pelo bridge. O lançador PowerShell também foi chamado por um cliente MCP real.
- Streamable HTTP: cliente oficial MCP conectado por TCP em loopback, mesmo catálogo/esquemas completos do STDIO e modelagem real pelo mesmo bridge.
- Segurança HTTP: autenticação ausente/incorreta/duplicada rejeitada; Host e Origin fora das listas rejeitados; Origin ausente aceita com autenticação; corpo acima de 64 KiB rejeitado; nenhuma ferramenta de execução arbitrária disponível.
- OAuth: testes com JWTs assinados por chave RSA local, validação de assinatura, issuer, audience, expiração, scopes e descoberta de recurso protegido. Esses testes não contatam um provedor de identidade real.
- Configuração: localhost como padrão; token ausente impede iniciar HTTP; porta configurada por ambiente; bind não local exige autorização explícita na configuração.
- `pip check`: nenhuma dependência quebrada.

A suíte completa com `FREECAD_INTEGRATION=1` terminou com **65 testes aprovados e 1 ignorado**, incluindo as regressões dos geradores e operações existentes. O relatório JUnit está em [transports-test-results.xml](../transports-test-results.xml). O teste de escape por symlink é ignorado quando o Windows não oferece o privilégio de criar symlinks. Há um aviso de depreciação de TestClient/httpx da versão instalada do Starlette; ele não impediu os testes.

## Peça criada por Streamable HTTP

Base de 40 × 30 × 6 mm, com furo passante Ø6 no centro. Foi criada por ferramentas MCP, subtraída, validada como um único sólido, salva, exportada, capturada e reaberta pelo MCP.

Volume teórico e verificado: **7.030,3539967061515 mm³**.

- [FCStd](../../modelos/transportes_http/placa_furada_http.FCStd)
- [STEP](../../modelos/transportes_http/placa_furada_http.step)
- [STL](../../modelos/transportes_http/placa_furada_http.stl)
- [Captura isométrica](../../modelos/transportes_http/placa_furada_http.png)
- [Chamadas e resultados reais](../http-integration-result.json)

As cópias versionadas têm nomes estáveis. Os caminhos absolutos originais de exportação constam do JSON de evidências.

## Suporte de fixação solicitado

Recriado usando exclusivamente as ferramentas `freecad_local` para a modelagem, gravação e exportação. A primeira tentativa de gravação havia falhado com `WinError 10061`; após restaurar o bridge, os três arquivos foram efetivamente gravados. O FCStd foi fechado, reaberto e validado novamente.

Base 120 × 80 × 10 mm; quatro furos Ø8 com centros (15,15), (105,15), (105,65), (15,65); ressalto central Ø30 com 20 mm acima da base; furo central Ø10 atravessando 30 mm.

Operações: caixa, cilindro do ressalto, uma união, quatro cilindros de corte e quatro subtrações, cilindro central e subtração final. Os objetos conservam nomes e referências Base/Tool. Resultado: **um sólido válido**, dimensões **120 × 80 × 30 mm**, volume **105.770,35315266428 mm³** (teórico: `96000 + 3110*pi`).

- [FCStd](../../modelos/suporte_teste.FCStd)
- [STEP](../../modelos/suporte_teste.step)
- [STL](../../modelos/suporte_teste.stl)
- [Captura isométrica](../../modelos/suporte_teste.png)

Originais em `C:/Users/CESS UFF/Projetos_CESS/FreCAD_mcp/modelos/`.

## Não validado remotamente

`tunnel-client` não foi localizado no PATH; o script retornou o diagnóstico real de ausência. Não foi instalado ou iniciado um túnel. Não foi verificado o RBAC da organização/workspace, configurado um emissor OAuth de produção ou executada uma chamada vinda do ChatGPT Web. Os testes locais não comprovam esses fluxos externos.

Veja [TRANSPORTS.md](TRANSPORTS.md) para as permissões necessárias e os passos manuais. Nenhum servidor foi publicado na internet e nenhuma regra de roteador/firewall foi criada.
