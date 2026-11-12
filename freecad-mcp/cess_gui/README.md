# Barra CESS — Desenho

Extensão Python para o FreeCAD instalado. Não exige compilar nem modificar o código-fonte C++ do FreeCAD. A pasta de fontes `FreeCAD/` não contém um executável nesta máquina; a aplicação utilizada é `C:/Program Files/FreeCAD 1.1/bin/freecad.exe`.

## Abrir com os botões

Na raiz do repositório, execute `Iniciar_FreeCAD_CESS.cmd`, ou:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\freecad-mcp\scripts\start.ps1
```

O script carrega o bridge MCP e a barra **CESS — Desenho**. Se FreeCAD estiver aberto sem a extensão, execute a macro gerada `.runtime/StartBridge.FCMacro` pelo menu **Macro > Macros**. A barra é carregada por essa macro; abrir diretamente o atalho comum do FreeCAD não garante carregamento automático. Nenhum arquivo foi instalado globalmente em Program Files ou na pasta de módulos do usuário.

## Centralizar

1. Saia da edição do Sketcher.
2. Na árvore, selecione primeiro o objeto que deseja mover.
3. Segurando Ctrl, selecione o objeto de referência.
4. Clique **Centralizar**; confira os nomes e escolha XY, X, Y, XZ, YZ, XYZ ou Z.
5. Clique **Centralizar** no diálogo. Ctrl+Z desfaz, Ctrl+Y refaz.

Exemplo: um quadrado de 40 × 40 mm centralizado em outro de 100 × 100 mm resulta em margens de 30 mm. A referência permanece fixa. Há um botão para inverter quem move e quem fica fixo.

O cálculo usa os centros das caixas delimitadoras no sistema global, sem alterar dimensões ou rotação. Para margens iguais, os retângulos precisam estar paralelos e um deve caber no outro. O movimento é pontual, não uma restrição paramétrica que se atualiza após redimensionar. Eixos não escolhidos permanecem inalterados.

Suporta objetos independentes, incluindo retângulos Draft e esboços completos. Não reposiciona geometrias individuais dentro do mesmo esboço: nesse caso, use restrições Sketcher. Recusa dependências entre os dois objetos, objetos anexados a suporte e posições controladas por expressões, para preservar esses vínculos.

## Cotas e textos

- **Colocar cotas:** ativa Draft e inicia `Draft_Dimension`. Indique o primeiro ponto, o segundo e a posição da linha de cota; use os encaixes para selecionar pontos exatos. Esc cancela a ferramenta. As opções do Draft também permitem outros tipos de cota.
- **Inserir texto:** ativa Draft e inicia `Draft_Text`. Use o painel de tarefas para definir posição, conteúdo e opções; depois ajuste as propriedades de visualização do objeto para fonte e tamanho quando necessário.

São anotações visíveis no modelo e salvas em FCStd. Não são gravações/recortes físicos no sólido nem páginas TechDraw para impressão. Uma cota livre feita por coordenadas pode não acompanhar mudanças de geometria; use cotas ligadas à geometria quando precisar dessa associação. STEP e STL exportam a geometria; não preservam essas anotações Draft como texto visível.

## Validação realizada

- Testes de cálculo e rejeição de coordenadas/eixos inválidos em `tests/test_alignment.py`.
- Smoke test dentro de uma instância gráfica real em `tests/freecad_gui_smoke.py`: centralização, desfazer/refazer, transformação de contêiner pai, cota de 100 mm, texto, ausência de barra duplicada e ativação dos comandos interativos Dimension/Text pelos comandos CESS.
- Barra e seus três botões confirmados na interface por Computer Use.
- Evidência resumida e sem caminhos pessoais em `../gui-validation.json`.

O teste de GUI exige FreeCAD com interface; não faz parte do pytest comum e não pode ser substituído por mocks para afirmar funcionamento real.
