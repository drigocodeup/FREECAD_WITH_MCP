# Barra CESS — Desenho

Extensão Python para o FreeCAD instalado. Não exige compilar nem modificar o código-fonte C++ do FreeCAD. A pasta de fontes `FreeCAD/` não contém um executável nesta máquina; a aplicação utilizada é `C:/Program Files/FreeCAD 1.1/bin/freecad.exe`.

Além da barra de desenho, a inicialização carrega os sete [geradores paramétricos](GENERATORS.md) e o módulo de [elétrica](ELECTRICAL.md).

## Abrir com os botões

Na raiz do repositório, execute `Iniciar_FreeCAD_CESS.cmd`, ou:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\freecad-mcp\scripts\start.ps1
```

O script carrega o bridge MCP e a barra **CESS — Desenho**. Se FreeCAD estiver aberto sem a extensão, execute a macro gerada `.runtime/StartBridge.FCMacro` pelo menu **Macro > Macros**. A barra é carregada por essa macro; abrir diretamente o atalho comum do FreeCAD não garante carregamento automático. Nenhum arquivo foi instalado globalmente em Program Files ou na pasta de módulos do usuário.

## Centralizar

### Dois retângulos dentro do mesmo Sketcher

1. Mantenha o esboço aberto em edição e clique **Centralizar**. Também funciona selecionando um esboço completo fora da edição.
2. O diálogo identifica os contornos retangulares; selecione quem move e a referência. Por padrão, move o menor para o maior. Não é necessário selecionar todos os vértices e linhas.
3. Escolha **XY**, **somente X** ou **somente Y**, nos eixos locais do esboço, e confirme.

O solver do Sketcher move o contorno preservando suas cotas e restrições. Dois quadrados de 40 e 50 mm ficam com margens de 5 mm, mantendo a referência fixa. Contornos que compartilham um canto também são identificados. Ctrl+Z desfaz e Ctrl+Y refaz.

São aceitos contornos fechados com quatro segmentos de linha paralelos aos eixos locais. Linhas de construção e pontos centrais não são tratados como retângulos. Se cotas de posição, fixações ou vínculos impedirem o deslocamento, a ferramenta recusa e reverte a operação; não remove restrições automaticamente. A centralização é pontual, sem criar vínculo paramétrico entre os centros.

### Dois objetos independentes

1. Saia da edição do Sketcher para mover objetos completos.
2. Na árvore, selecione primeiro o objeto que deseja mover.
3. Segurando Ctrl, selecione o objeto de referência.
4. Clique **Centralizar**; confira os nomes e escolha XY, X, Y, XZ, YZ, XYZ ou Z.
5. Clique **Centralizar** no diálogo. Ctrl+Z desfaz, Ctrl+Y refaz.

Exemplo: um quadrado de 40 × 40 mm centralizado em outro de 100 × 100 mm resulta em margens de 30 mm. A referência permanece fixa. Há um botão para inverter quem move e quem fica fixo.

O cálculo usa os centros das caixas delimitadoras no sistema global, sem alterar dimensões ou rotação. Para margens iguais, os retângulos precisam estar paralelos e um deve caber no outro. O movimento é pontual, não uma restrição paramétrica que se atualiza após redimensionar. Eixos não escolhidos permanecem inalterados.

Suporta objetos independentes, incluindo retângulos Draft e esboços completos. Recusa dependências entre os dois objetos, objetos anexados a suporte e posições controladas por expressões, para preservar esses vínculos. Dentro do mesmo esboço, use o modo Sketcher descrito acima.

## Cotas e textos

- **Colocar cotas:** ativa Draft e inicia `Draft_Dimension`. Indique o primeiro ponto, o segundo e a posição da linha de cota; use os encaixes para selecionar pontos exatos. Esc cancela a ferramenta. As opções do Draft também permitem outros tipos de cota.
- **Inserir texto:** ativa Draft e inicia `Draft_Text`. Use o painel de tarefas para definir posição, conteúdo e opções; depois ajuste as propriedades de visualização do objeto para fonte e tamanho quando necessário.

São anotações visíveis no modelo e salvas em FCStd. Não são gravações/recortes físicos no sólido nem páginas TechDraw para impressão. Uma cota livre feita por coordenadas pode não acompanhar mudanças de geometria; use cotas ligadas à geometria quando precisar dessa associação. STEP e STL exportam a geometria; não preservam essas anotações Draft como texto visível.

## Validação realizada

- Testes de cálculo e rejeição de coordenadas/eixos inválidos em `tests/test_alignment.py`.
- Identificação de retângulos, canto compartilhado e contornos incompletos em `tests/test_sketch_center.py`. Teste gráfico/solver real em `tests/freecad_sketch_center.py`: 40/50 mm, referência fixa, cotas preservadas, XY/X/Y, desfazer/refazer, bloqueio por cota de posição e clique no próprio botão da barra durante edição. Evidência: `sketch-center-validation.json`.
- Smoke test dentro de uma instância gráfica real em `tests/freecad_gui_smoke.py`: centralização, desfazer/refazer, transformação de contêiner pai, cota de 100 mm, texto, ausência de barra duplicada e ativação dos comandos interativos Dimension/Text pelos comandos CESS.
- Barra e seus três botões confirmados na interface por Computer Use.
- Evidência resumida e sem caminhos pessoais em `../gui-validation.json`.

O teste de GUI exige FreeCAD com interface; não faz parte do pytest comum e não pode ser substituído por mocks para afirmar funcionamento real.
