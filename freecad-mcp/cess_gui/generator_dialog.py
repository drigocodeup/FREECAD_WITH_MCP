"""One validated parameter dialog shared by the five generator commands."""
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui
try:
    from PySide import QtWidgets
except ImportError:
    QtWidgets = QtGui
from cess_gui.generator_specs import SPECS, defaults


class GeneratorDialog(QtWidgets.QDialog):
    def __init__(self, kind):
        super().__init__(Gui.getMainWindow())
        self.kind = kind
        self.result_objects = None
        self.setWindowTitle('CESS — ' + SPECS[kind][0])
        self.setMinimumWidth(540)
        layout = QtWidgets.QVBoxLayout(self)
        notes = {
            'fastener':'Parafuso e porca com rosca helicoidal 3D real de 60 graus. Cabeca Allen ou sextavada. Medidas em mm; folga diametral ajustavel.',
            'gear_pair':'Dois eixos paralelos. Relacao = voltas entrada:saida: 2:1 reduz; 1:2 aumenta. Caixa com tampa removivel opcional.',
            'gear':'Engrenagem cilindrica de dentes retos e perfil evolvente. Dimensoes em mm.',
            'box':'Base aberta e tampa com guia de encaixe, separadas lado a lado. Folga por lado.',
            'letters':'Letras ocas com fundo e frente aberta. Frente plana separada opcional, para colagem.',
            'numbers':'Numeros ocos com fundo e frente aberta. Frente plana separada opcional, para colagem.',
            'organizer':'Bandeja aberta com compartimentos iguais em linhas e colunas.'}
        explanation = QtWidgets.QLabel(notes[kind] + '\nEdite depois em Parametros, na arvore do documento.')
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        form = QtWidgets.QFormLayout()
        self.widgets = {}
        initial = defaults(kind)
        for field in SPECS[kind][1]:
            if field.type == 'enum':
                widget = QtWidgets.QComboBox()
                widget.addItems(list(field.choices))
                widget.setCurrentText(initial[field.key])
            elif field.type == 'bool':
                widget = QtWidgets.QCheckBox()
                widget.setChecked(initial[field.key])
            elif field.type in ('text','font'):
                widget = QtWidgets.QLineEdit(str(initial[field.key]))
            elif field.type == 'int':
                widget = QtWidgets.QSpinBox()
                widget.setRange(int(field.minimum),int(field.maximum))
                widget.setValue(initial[field.key])
            else:
                widget = QtWidgets.QDoubleSpinBox()
                widget.setDecimals(3)
                widget.setRange(field.minimum,field.maximum)
                widget.setValue(initial[field.key])
                widget.setSuffix(' °' if field.type == 'angle' else ' mm')
            widget.setObjectName('CESS_Input_' + field.key)
            self.widgets[field.key] = widget
            if field.type == 'font':
                row = QtWidgets.QHBoxLayout()
                row.addWidget(widget)
                browse = QtWidgets.QPushButton('Escolher...')
                browse.clicked.connect(self.choose_font)
                row.addWidget(browse)
                form.addRow(field.label,row)
            else:
                form.addRow(field.label,widget)
        layout.addLayout(form)
        if kind == 'gear_pair':
            self.summary = QtWidgets.QLabel()
            self.summary.setWordWrap(True)
            self.summary.setObjectName('CESS_GearPairSummary')
            layout.addWidget(self.summary)
        self.feedback = QtWidgets.QLabel()
        self.feedback.setWordWrap(True)
        layout.addWidget(self.feedback)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.create_button = buttons.button(QtWidgets.QDialogButtonBox.Ok)
        self.create_button.setText('Gerar modelo')
        buttons.button(QtWidgets.QDialogButtonBox.Cancel).setText('Cancelar')
        buttons.accepted.connect(self.generate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        if kind == 'gear_pair':
            for field in SPECS[kind][1]:
                widget = self.widgets[field.key]
                signal = widget.textChanged if field.type=='text' else (widget.toggled if field.type=='bool' else widget.valueChanged)
                signal.connect(self.update_summary)
            self.update_summary()
        if kind == 'fastener':
            self.widgets['head_type'].currentTextChanged.connect(self.update_fastener_controls)
            self.update_fastener_controls()

    def update_fastener_controls(self, *args):
        is_allen=self.widgets['head_type'].currentText()=='allen'
        for key in ('socket_size','socket_depth'):
            self.widgets[key].setEnabled(is_allen)

    def update_summary(self, *args):
        try:
            from cess_gui.generator_specs import validate
            from cess_gui.gear_sets import gear_pair_layout
            info = gear_pair_layout(validate('gear_pair',self.values()))
            self.summary.setText(f"{info['mode']} {info['ratio']} | Dentes entrada/saida: {info['input_teeth']}/{info['output_teeth']}\n"
                                 f"Entre eixos: {info['center_distance']:.3f} mm | Saida gira no sentido oposto.\n"
                                 'Eixos lisos e furos livres; fixacao por chaveta e rolamentos nao incluidos.')
            self.create_button.setEnabled(True)
        except ValueError as error:
            self.summary.setText(str(error))
            self.create_button.setEnabled(False)

    def choose_font(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self,'Fonte do texto',self.widgets['font_file'].text(),
                                                          'Fontes (*.ttf *.otf)')
        if filename:
            self.widgets['font_file'].setText(filename)

    def values(self):
        result = {}
        for field in SPECS[self.kind][1]:
            widget = self.widgets[field.key]
            if field.type == 'enum':
                result[field.key] = widget.currentText()
            elif field.type == 'bool':
                result[field.key] = widget.isChecked()
            elif field.type in ('text','font'):
                result[field.key] = widget.text()
            else:
                result[field.key] = widget.value()
        return result

    def generate(self):
        self.create_button.setEnabled(False)
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            from cess_gui.generators import create_generator
            self.result_objects = create_generator(self.kind,self.values())
            view = Gui.activeDocument().activeView()
            view.viewAxonometric()
            view.fitAll()
            Gui.Selection.clearSelection()
            Gui.getMainWindow().statusBar().showMessage('Modelo criado. Edite Parametros na arvore; Ctrl+Z desfaz.',15000)
            self.accept()
        except Exception as error:
            self.feedback.setText(str(error))
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
            self.create_button.setEnabled(True)


class GeneratorCommand:
    def __init__(self, kind):
        self.kind = kind

    def GetResources(self):
        from pathlib import Path
        return {'MenuText':SPECS[self.kind][0], 'ToolTip':'Gerar '+SPECS[self.kind][0].lower()+' com parametros editaveis.',
                'Pixmap':str(Path(__file__).parent / 'icons' / (self.kind+'.svg'))}

    def IsActive(self):
        return True

    def Activated(self):
        if App.ActiveDocument and Gui.activeDocument().getInEdit():
            QtWidgets.QMessageBox.information(Gui.getMainWindow(),'CESS','Feche a edicao atual antes de gerar o modelo.')
            return
        GeneratorDialog(self.kind).exec_()


COMMANDS = {'CESS_Engrenagem':'gear','CESS_ConjuntoEngrenagens':'gear_pair','CESS_ParafusoPorca':'fastener','CESS_CaixaTampa':'box','CESS_LetraCaixa':'letters',
            'CESS_NumeroCaixa':'numbers','CESS_Organizador':'organizer'}
_registered = []


def install():
    window = Gui.getMainWindow()
    existing = window.findChild(QtWidgets.QToolBar,'CESS_GeneratorsToolbar')
    toolbar = existing if existing is not None else QtWidgets.QToolBar('CESS — Geradores',window)
    toolbar.setObjectName('CESS_GeneratorsToolbar')
    toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
    toolbar.setIconSize(QtCore.QSize(24,24))
    for name, kind in COMMANDS.items():
        if any(action.objectName()==name for action in toolbar.actions()):
            continue
        command = GeneratorCommand(kind)
        Gui.addCommand(name,command)
        resources = command.GetResources()
        action = toolbar.addAction(QtGui.QIcon(resources['Pixmap']),resources['MenuText'])
        action.setObjectName(name)
        action.setToolTip(resources['ToolTip'])
        action.triggered.connect(lambda checked=False,name=name:Gui.runCommand(name,0))
        _registered.append(command)
    if existing is None:
        window.addToolBarBreak(QtCore.Qt.TopToolBarArea)
        window.addToolBar(QtCore.Qt.TopToolBarArea,toolbar)
    toolbar.show()
    return toolbar
