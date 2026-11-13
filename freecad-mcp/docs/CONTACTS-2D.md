# Biblioteca de contatos 2D do CADe_SIMU

A biblioteca elétrica passa de 17 para **77 símbolos vetoriais 2D**, preservando os identificadores anteriores. Os **66 itens das quatro barras de referência** foram mapeados; os outros 11 símbolos anteriores continuam disponíveis. Não são sólidos, peças 3D ou componentes simulados.

| Barra de referência | Itens | Conteúdo |
|---|---:|---|
| Contatos auxiliares e temporizados | 16 | NA, NF, NA+NF e comutador; instantâneos, retardo na energização, desenergização e ambos |
| Acionamentos | 24 | Botoeiras, cogumelos, interruptores, fins de curso, térmicos, seletores I-0-II/I-II-III, cruzamento e acionador de botoeira |
| Contatores e interruptores de potência | 10 | Um a quatro polos, contator tripolar NF e indicação de intertravamento mecânico |
| Sensores | 16 | Indutivos, capacitivos, magnéticos, barreira/emissor/receptor fotoelétrico, pressostatos, vacuostatos e termostatos |

NA+NF tem quatro terminais independentes. O comutador tem três: comum 11, NF 12 e NA 14. Contatos térmicos usam 95/96 e 97/98. Os polos de potência possuem terminais numerados distintos. Acionador de botoeira e intertravamento são indicações gráficas, sem terminais elétricos. O emissor fotoelétrico possui alimentação A1/A2; não foi representado como contato NA.

## Conferência da referência

A instalação local CADe_SIMU 4.0 foi inspecionada de duas formas:

- Navegação real na janela aberta: menu de barras, contatos auxiliares/temporizados, acionamentos, sensores e potência. A prévia do comutador mostrou 11/12/14. As seleções foram canceladas sem inserir ou salvar alterações no circuito do usuário.
- Leitura estática dos recursos PE de strings e barras 175, 189, 191 e 215, sem carregar ou executar o binário pelo script. Todos os 66 IDs dessas barras aparecem no [inventário](cadesimu-contacts-inventory.json), com hash SHA-256 do executável consultado.

O recurso espanhol do pressostato 33254 repete NA; os recursos inglês/italiano o identificam como NF. A representação usa NF. Os rótulos e IDs foram cruzados com a navegação; não se afirma inspeção visual individual de cada um dos 66 itens.

Os vetores são implementações próprias equivalentes para desenho. Não se trata de extração dos desenhos binários, reprodução visual exata ou cópia integral de todas as bibliotecas do CADe_SIMU. Recursos pneumáticos, lógicos, dispositivos físicos 3D e simulação ficam fora deste escopo.

## Usar e consultar

Abra **CESS — Elétrica → Nova prancha elétrica** ou **Editar diagrama**. A busca da biblioteca filtra pelo nome/categoria; experimente `temporizado`, `fim de curso`, `pressostato` ou `potencia`. As ferramentas MCP são as mesmas sete ferramentas elétricas e o catálogo total permanece em 43 ferramentas, compartilhadas por STDIO e HTTP.

O catálogo A0 com todos os símbolos fica em [`modelos/eletrica/catalogo_contatos_2d.FCStd`](../../modelos/eletrica/catalogo_contatos_2d.FCStd), acompanhado de PDF, SVG, PNG e JSON.

## Validação

Os testes percorrem todos os símbolos nos dez formatos/orientações e quatro rotações, conferem topologia dos terminais e renderização SVG. O teste gráfico real inseriu um comutador temporizado e um fim de curso NA+NF e conectou os terminais com mouse. Os clientes MCP reais criaram, exportaram, salvaram e reabriram pranchas nos dois transportes, e geraram o catálogo A0 completo.

A ocorrência anterior de encerramento nativo na regressão dos geradores mecânicos permanece registrada em [VALIDATION-ELECTRICAL.md](VALIDATION-ELECTRICAL.md); esses testes pesados não foram repetidos nesta ampliação de símbolos.

Resultado desta ampliação: **122 testes aprovados e 1 ignorado**, com os três testes MCP pesados de geradores mecânicos excluídos. Isso inclui **32 testes elétricos**. Evidências: `contacts-test-summary.json`, `contacts-gui-validation.json`, `contacts-stdio-validation.json` e `contacts-http-validation.json`. O catálogo completo foi reaberto na GUI com 77 símbolos e zero fios; seu PDF A0 foi aberto pelo leitor do Windows e revisado visualmente.
