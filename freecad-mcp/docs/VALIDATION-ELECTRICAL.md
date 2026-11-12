# Validação do módulo elétrico

Ambiente: Windows, FreeCAD 1.1.1 instalado, Python embarcado 3.11.14, Qt 6.8.3/PySide6, servidor Python 3.12.10 e SDK MCP 1.30.0. O código-fonte original do FreeCAD e os arquivos do CADe_SIMU foram preservados.

## Execução real

- A interface gráfica inseriu contato NA e bobina por eventos de mouse Qt, conectou terminais, alterou posição pelas propriedades e desfez a mudança. O fio acompanhou o componente. O diálogo de prancha alterou formato e título.
- Foram criadas páginas TechDraw nos dez formatos A0–A4, retrato e paisagem, com dimensões nativas verificadas. Os dez PDFs foram abertos pelo leitor do Windows; todos têm uma página e dimensão física dentro de 0,3 mm do papel solicitado. Esse limite considera o arredondamento do Qt para pontos PDF.
- O exemplo de partida/parada com selo contém 14 símbolos e 15 fios. FCStd salvo e reaberto, contagens e referências página/template preservadas, edição do responsável e desfazer conferidos. O arquivo FCStd contém o SVG incorporado.
- Clientes do SDK oficial criaram diagramas reais em STDIO e Streamable HTTP autenticado, inseriram símbolos/fio, atualizaram posição e carimbo, rejeitaram posições fora da margem e exportação com `../`, exportaram PDF/SVG/PNG/JSON e salvaram/reabriram FCStd sem mudança do desenho.
- O catálogo dos dois transportes contém 43 ferramentas. Não foi acrescentado endpoint para executar Python arbitrário.
- As imagens do editor, PNG exportado e PDF renderizado foram inspecionadas visualmente: diagrama legível, margens e quadro inferior preservados.

Evidências: `electrical-gui-validation.json`, `electrical-stdio-validation.json`, `electrical-http-validation.json`, `electrical-pdf-validation.json`. Os caminhos absolutos nesses relatórios identificam os arquivos da execução local. O exemplo curado está em [`modelos/eletrica`](../../modelos/eletrica).

## Limites e ocorrência na regressão

Após reiniciar novamente, a execução com `--ignore=tests/test_gear_pair_mcp.py --ignore=tests/test_generators_mcp.py` terminou com **120 testes aprovados e 1 ignorado**, incluindo os 29 testes elétricos, os dois transportes, os parafusos e as operações CAD básicas reais. O teste ignorado depende do privilégio Windows para criar links simbólicos. O aviso de depreciação Starlette/httpx é anterior ao módulo. Essa execução selecionada não substitui o resultado da regressão completa descrito abaixo.

Na primeira execução da regressão completa, a aplicação FreeCAD encerrou durante o gerador anterior de conjuntos de engrenagens: a chamada retornou `WinError 10054`, seguida de `WinError 10061` nas chamadas posteriores. Após reiniciar pelo script normal, o teste de engrenagens passou isoladamente. A segunda execução completa encerrou durante os cinco geradores anteriores e terminou com **118 testes aprovados, 4 falhas e 1 ignorado**. As falhas posteriores foram consequência da conexão perdida. Os dumps `freecad.exe.520.dmp` e `freecad.exe.16908.dmp` registram exceção `0xc0000409` em `C:\Windows\System32\UIAutomationCore.DLL`, deslocamento `0x2d3555`. Esse registro não determina a causa raiz. A regressão completa não foi declarada aprovada e a falha nativa não foi apresentada como corrigida.

Não foram testadas impressão física, outras versões do FreeCAD ou outro computador. Não há simulação elétrica, importador `.cad` do CADe_SIMU, verificação de continuidade ou certificação normativa. Os símbolos vetoriais são próprios, inspirados na organização funcional das referências locais. A numeração das folhas é editável; cada prancha é um controlador/página independente, sem referências cruzadas automáticas entre folhas.

## Reproduzir

1. Inicie o bridge com `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/start.ps1`.
2. Execute `$env:FREECAD_INTEGRATION='1'; .venv/Scripts/python.exe -m pytest -q` no diretório instalado.
3. Para o teste da interface, carregue `tests/freecad_electrical_gui.py` pelo Python embarcado e agende `run(project)` com `QTimer.singleShot` após a macro de entrada terminar. Não rode o teste de mouse dentro do cursor de espera de `--single-instance`.
4. Para conferir um PDF, execute `powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests/render_electrical_pdf.ps1 -InputPdf <arquivo-em-modelos.pdf> -OutputPng <imagem-em-modelos.png>`.
