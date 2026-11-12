"""FreeCAD GUI commands. Import/install only from FreeCAD's Qt main thread."""
from pathlib import Path
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui
try:
    from PySide import QtWidgets
except ImportError:
    QtWidgets = QtGui
from cess_gui.alignment import alignment_delta

TOOLBAR_NAME = 'CESS_DrawingToolbar'
COMMANDS = ('CESS_Centralizar', 'CESS_Cotas', 'CESS_Texto')
_commands = []


def world_center(obj):
    if not hasattr(obj, 'Shape') or obj.Shape.isNull() or not hasattr(obj, 'Placement'):
        raise ValueError('Selecione objetos geometricos, como retangulos, pecas ou esbocos completos.')
    shape = obj.Shape.copy()
    parent = obj.getGlobalPlacement().multiply(obj.Placement.inverse())
    shape.Placement = parent.multiply(shape.Placement)
    return shape.BoundBox.Center


def center_objects(moving, reference, axes='XY'):
    if moving == reference or moving.Document != reference.Document:
        raise ValueError('Selecione dois objetos diferentes do mesmo documento.')
    if moving in reference.OutListRecursive or reference in moving.OutListRecursive:
        raise ValueError('Os objetos possuem dependencia entre si. Selecione objetos independentes.')
    if hasattr(moving, 'MapMode') and str(moving.MapMode) != 'Deactivated':
        raise ValueError('O objeto esta anexado a um suporte. Ajuste o Attachment Offset ou desanexe-o primeiro.')
    if any(str(path).startswith(('Placement', 'AttachmentOffset')) for path, expression in moving.ExpressionEngine):
        raise ValueError('A posicao possui expressoes. Ajuste as expressoes para preservar o vinculo.')
    doc = moving.Document
    doc.recompute()
    original = world_center(moving)
    target = world_center(reference)
    delta = App.Vector(*alignment_delta(tuple(original), tuple(target), axes))
    parent = moving.getGlobalPlacement().multiply(moving.Placement.inverse())
    local_delta = parent.Rotation.inverted().multVec(delta)
    doc.openTransaction('CESS: centralizar objetos')
    try:
        placement = App.Placement(moving.Placement)
        placement.Base = placement.Base.add(local_delta)
        moving.Placement = placement
        doc.recompute()
        actual = world_center(moving)
        remaining = alignment_delta(tuple(actual), tuple(target), axes)
        if any(abs(value) > 1e-6 for value in remaining):
            raise ValueError('O objeto nao aceitou a posicao. Verifique suportes e restricoes.')
        doc.commitTransaction()
    except Exception:
        doc.abortTransaction()
        raise
    return {'moving': moving.Name, 'reference': reference.Name, 'axes': axes,
            'translation_mm': list(delta), 'center': list(actual)}


class CenterDialog(QtWidgets.QDialog):
    def __init__(self, moving, reference):
        super().__init__(Gui.getMainWindow())
        self.setWindowTitle('Centralizar objetos')
        self.setMinimumWidth(450)
        self.moving, self.reference = moving, reference
        layout = QtWidgets.QVBoxLayout(self)
        explanation = QtWidgets.QLabel(
            'Alinha os centros dos limites geometricos, sem alterar tamanho ou rotacao.\n'
            'Para margens iguais, use retangulos paralelos e um menor que o outro.')
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        self.objects_label = QtWidgets.QLabel()
        layout.addWidget(self.objects_label)
        swap = QtWidgets.QPushButton('Inverter: quem move / referencia')
        swap.clicked.connect(self.swap)
        layout.addWidget(swap)
        form = QtWidgets.QFormLayout()
        self.axes = QtWidgets.QComboBox()
        for text, data in [('Horizontal e vertical — XY', 'XY'), ('Somente X', 'X'),
                           ('Somente Y', 'Y'), ('Plano XZ', 'XZ'), ('Plano YZ', 'YZ'),
                           ('Todos os eixos — XYZ', 'XYZ'), ('Somente Z', 'Z')]:
            self.axes.addItem(text, data)
        form.addRow('Centralizar em:', self.axes)
        layout.addLayout(form)
        self.feedback = QtWidgets.QLabel()
        self.feedback.setWordWrap(True)
        layout.addWidget(self.feedback)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttons.button(QtWidgets.QDialogButtonBox.Ok).setText('Centralizar')
        buttons.button(QtWidgets.QDialogButtonBox.Cancel).setText('Cancelar')
        buttons.accepted.connect(self.apply)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.refresh()

    def refresh(self):
        self.objects_label.setText(f'Mover: {self.moving.Label} ({self.moving.Name})\n'
                                   f'Referencia fixa: {self.reference.Label} ({self.reference.Name})')

    def swap(self):
        self.moving, self.reference = self.reference, self.moving
        self.refresh()

    def apply(self):
        try:
            result = center_objects(self.moving, self.reference, self.axes.currentData())
            Gui.getMainWindow().statusBar().showMessage(
                f"{self.moving.Label} centralizado em {result['axes']}. Ctrl+Z desfaz.", 12000)
            self.accept()
        except Exception as error:
            self.feedback.setText(str(error))


def warn(message):
    QtWidgets.QMessageBox.information(Gui.getMainWindow(), 'CESS — Desenho', message)


class CenterCommand:
    def GetResources(self):
        return {'MenuText': 'Centralizar', 'ToolTip': 'Selecione primeiro o objeto que move e depois a referencia com Ctrl. Alinhe os centros.',
                'Pixmap': str(Path(__file__).parent / 'icons/center.svg')}

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        selected = Gui.Selection.getSelection()
        if len(selected) != 2:
            warn('Selecione dois objetos na arvore, usando Ctrl:\n'
                 '1. Objeto que sera movido (ex.: quadrado menor).\n'
                 '2. Objeto de referencia (ex.: quadrado maior).\n\n'
                 'Selecione objetos completos. Geometrias dentro do mesmo Sketcher '
                 'precisam de restricoes do esboco.')
            return
        if Gui.activeDocument().getInEdit():
            warn('Feche a edicao do esboco ou da tarefa antes de mover objetos completos.')
            return
        CenterDialog(*selected).exec_()


class DraftCommand:
    def __init__(self, native, title, tooltip, icon):
        self.native, self.title, self.tooltip, self.icon = native, title, tooltip, icon

    def GetResources(self):
        return {'MenuText': self.title, 'ToolTip': self.tooltip,
                'Pixmap': str(Path(__file__).parent / 'icons' / self.icon)}

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        if App.ActiveDocument is None:
            warn('Crie ou abra um documento antes de inserir cotas ou texto.')
            return
        if Gui.activeDocument().getInEdit():
            warn('Feche a edicao do esboco antes de inserir anotacoes Draft na vista do modelo.')
            return
        try:
            # Initializes the native commands, snapping and the interactive task panel.
            Gui.activateWorkbench('DraftWorkbench')
            Gui.runCommand(self.native, 0)
        except Exception as error:
            warn('Nao foi possivel iniciar a ferramenta Draft:\n' + str(error))


def install():
    from cess_gui.generator_dialog import install as install_generators
    install_generators()
    window = Gui.getMainWindow()
    existing = window.findChild(QtWidgets.QToolBar, TOOLBAR_NAME)
    if existing is not None:
        existing.show()
        return existing
    commands = [CenterCommand(),
                DraftCommand('Draft_Dimension', 'Colocar cotas',
                             'Cotas Draft: marque os pontos medidos e a posicao da cota. Esc cancela.', 'dimension.svg'),
                DraftCommand('Draft_Text', 'Inserir texto',
                             'Texto Draft: escolha posicao, conteudo e tamanho no painel de tarefas. Esc cancela.', 'text.svg')]
    toolbar = QtWidgets.QToolBar('CESS — Desenho', window)
    toolbar.setObjectName(TOOLBAR_NAME)
    toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
    toolbar.setIconSize(QtCore.QSize(24, 24))
    for name, command in zip(COMMANDS, commands):
        Gui.addCommand(name, command)
        resources = command.GetResources()
        action = toolbar.addAction(QtGui.QIcon(resources['Pixmap']), resources['MenuText'])
        action.setObjectName(name)
        action.setToolTip(resources['ToolTip'])
        action.triggered.connect(lambda checked=False, name=name: Gui.runCommand(name, 0))
    _commands.extend(commands)
    window.addToolBar(QtCore.Qt.TopToolBarArea, toolbar)
    toolbar.show()
    window.statusBar().showMessage('CESS — Desenho: Centralizar | Colocar cotas | Inserir texto', 15000)
    return toolbar
