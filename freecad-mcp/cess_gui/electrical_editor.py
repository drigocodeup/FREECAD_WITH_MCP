"""Native Qt electrical drafting editor. All edits persist in the FreeCAD document."""
from copy import deepcopy
import json
from pathlib import Path
import textwrap
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore,QtGui,QtSvg
try:
    from PySide import QtSvgWidgets
except ImportError:
    QtSvgWidgets=QtSvg
try:
    from PySide import QtWidgets
except ImportError:
    QtWidgets=QtGui
from bridge.geometry import safe_path
from cess_gui.electrical_model import (PAPERS,META,new_drawing,validate,dimensions,drawing_bounds,
    add_symbol,add_wire,remove_item,next_id,pin_position,endpoint,wire_points)
from cess_gui.electrical_symbols import CATALOG
from cess_gui.electrical_svg import render_svg,standalone_symbol
from cess_gui.electrical_project import PROJECT,is_sheet,read_model,apply_model,create_sheet,export_sheet

_editors=[]
_commands=[]
META_LABELS={'company':'Empresa / escola','title':'Titulo','project':'Projeto / codigo','author':'Responsavel',
             'checked':'Verificado por','revision':'Revisao','date':'Data','sheet':'Folha','sheets':'Total de folhas'}


def models_root():
    settings=json.loads((PROJECT/'config/settings.json').read_text(encoding='utf-8'))
    return (PROJECT/settings['models_directory']).resolve()


class SheetDialog(QtWidgets.QDialog):
    def __init__(self,model=None):
        super().__init__(Gui.getMainWindow())
        self.original=deepcopy(model or new_drawing());self.result_model=None
        self.setWindowTitle('CESS - Prancha de projeto eletrico');self.setMinimumWidth(560)
        layout=QtWidgets.QVBoxLayout(self);form=QtWidgets.QFormLayout()
        self.paper=QtWidgets.QComboBox();self.paper.addItems(list(PAPERS));self.paper.setCurrentText(self.original['paper'])
        self.paper.setObjectName('CESS_ElectricalPaper')
        self.orientation=QtWidgets.QComboBox()
        self.orientation.addItem('Paisagem','landscape');self.orientation.addItem('Retrato','portrait')
        self.orientation.setCurrentIndex(0 if self.original['orientation']=='landscape' else 1)
        form.addRow('Formato',self.paper);form.addRow('Orientacao',self.orientation)
        self.fields={}
        for key,label in META_LABELS.items():
            widget=QtWidgets.QLineEdit(self.original['metadata'][key]);widget.setMaxLength(80 if key=='title' else 50)
            widget.setObjectName('CESS_ElectricalMeta_'+key);self.fields[key]=widget;form.addRow(label,widget)
        self.grid=QtWidgets.QDoubleSpinBox();self.grid.setRange(.5,20);self.grid.setValue(self.original['grid']);self.grid.setSuffix(' mm')
        form.addRow('Grade de desenho',self.grid);layout.addLayout(form)
        layout.addWidget(QtWidgets.QLabel('Margem esquerda: 20 mm; demais: 10 mm. Quadro inferior: 180 x 35 mm.'))
        self.feedback=QtWidgets.QLabel();self.feedback.setWordWrap(True);layout.addWidget(self.feedback)
        buttons=QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok|QtWidgets.QDialogButtonBox.Cancel)
        buttons.button(QtWidgets.QDialogButtonBox.Ok).setText('Aplicar prancha')
        buttons.accepted.connect(self.apply);buttons.rejected.connect(self.reject);layout.addWidget(buttons)

    def apply(self):
        try:
            model=deepcopy(self.original)
            model.update(paper=self.paper.currentText(),orientation=self.orientation.currentData(),grid=self.grid.value(),
                         metadata={key:widget.text() for key,widget in self.fields.items()})
            self.result_model=validate(model);self.accept()
        except Exception as error:self.feedback.setText(str(error))


def painter_path(points):
    path=QtGui.QPainterPath(QtCore.QPointF(*points[0]))
    for p in points[1:]:path.lineTo(QtCore.QPointF(*p))
    return path


class SymbolItem(QtSvgWidgets.QGraphicsSvgItem):
    def __init__(self,component,editor):
        super().__init__();self.editor=editor;self.component_id=component['id'];self.moved=False
        self.renderer=QtSvg.QSvgRenderer(QtCore.QByteArray(standalone_symbol(component).encode('utf-8')))
        self.setSharedRenderer(self.renderer);self.setPos(component['x']-12,component['y']-14)
        self.setFlags(QtWidgets.QGraphicsItem.ItemIsSelectable|QtWidgets.QGraphicsItem.ItemIsMovable)
        self.setData(0,'symbol');self.setData(1,self.component_id);self.setZValue(2)
        self.label_width=max(len(component['tag'])*1.55,min(len(component['description']),22)*1.1)+3
    def shape(self):
        path=QtGui.QPainterPath();path.addRect(3,3,18,24);path.addRect(19,8,self.label_width,22)
        return path
    def mouseMoveEvent(self,event):
        super().mouseMoveEvent(event);self.moved=True
        grid=self.editor.model['grid'];x=round((self.pos().x()+12)/grid)*grid;y=round((self.pos().y()+14)/grid)*grid
        self.setPos(x-12,y-14)
        component=next(s for s in self.editor.model['symbols'] if s['id']==self.component_id)
        component.update(x=x,y=y);self.editor.scene.refresh_wires()
    def mouseReleaseEvent(self,event):
        super().mouseReleaseEvent(event)
        if self.moved:
            self.moved=False;QtCore.QTimer.singleShot(0,lambda:self.editor.commit(self.editor.model,'Mover simbolo'))


class WireItem(QtWidgets.QGraphicsPathItem):
    def shape(self):
        stroker=QtGui.QPainterPathStroker();stroker.setWidth(2)
        return stroker.createStroke(self.path())


class DiagramScene(QtWidgets.QGraphicsScene):
    def __init__(self,editor):
        super().__init__(editor);self.editor=editor;self.mode='select';self.kind=None;self.pending=None
        self.preview=None;self.wire_items={};self.setBackgroundBrush(QtGui.QColor('#d7dde4'))
    def reference(self,p):
        best=None;distance=2.5
        for symbol in self.editor.model['symbols']:
            for pin,_,_ in CATALOG[symbol['kind']]['pins']:
                x,y=pin_position(symbol,pin);d=((x-p.x())**2+(y-p.y())**2)**.5
                if d<distance:distance=d;best={'symbol':symbol['id'],'pin':pin}
        if best:return best
        grid=self.editor.model['grid']
        return {'point':[round(p.x()/grid)*grid,round(p.y()/grid)*grid]}
    def refresh_wires(self):
        for wire in self.editor.model['wires']:
            if wire['id'] in self.wire_items:self.wire_items[wire['id']].setPath(painter_path(wire_points(self.editor.model,wire)))
    def cancel(self):
        self.mode='select';self.pending=None;self.kind=None
        if self.preview is not None:self.removeItem(self.preview);self.preview=None
        self.editor.message('Selecionar / mover. Arraste simbolos; os fios acompanham os terminais.')
    def mousePressEvent(self,event):
        if event.button()==QtCore.Qt.RightButton:self.cancel();event.accept();return
        if event.button()==QtCore.Qt.LeftButton and self.mode!='select':
            try:
                ref=self.reference(event.scenePos());point=endpoint(self.editor.model,ref)
                if self.mode=='symbol':
                    model,_=add_symbol(self.editor.model,self.kind,*point)
                    self.editor.commit(model,'Inserir simbolo')
                elif self.mode=='wire':
                    if self.pending is None:
                        self.pending=ref;self.editor.message('Clique no terminal ou ponto final. Esc cancela.')
                    else:
                        model,_=add_wire(self.editor.model,self.pending,ref)
                        self.pending=None;self.editor.commit(model,'Desenhar conexao')
                elif self.mode=='note':
                    value,ok=QtWidgets.QInputDialog.getMultiLineText(self.editor,'Texto da prancha','Anotacao:')
                    if ok and value:
                        model=deepcopy(self.editor.model);x,y=point
                        chars=max(5,min(70,int((drawing_bounds(model)[2]-x)/(3*.65))))
                        value='\n'.join(textwrap.fill(row,chars) for row in value.splitlines())
                        model['notes'].append(dict(id=next_id(model,'N'),text=value,x=x,y=y,size=3))
                        self.editor.commit(model,'Inserir texto')
                event.accept();return
            except Exception as error:self.editor.message(str(error),True);event.accept();return
        super().mousePressEvent(event)
    def mouseMoveEvent(self,event):
        if self.mode=='wire' and self.pending is not None:
            point=endpoint(self.editor.model,self.reference(event.scenePos()))
            a=endpoint(self.editor.model,self.pending);points=[a,[a[0],point[1]],point]
            if self.preview is None:self.preview=self.addPath(painter_path(points),QtGui.QPen(QtGui.QColor('#3977bc'),.35,QtCore.Qt.DashLine))
            else:self.preview.setPath(painter_path(points))
        super().mouseMoveEvent(event)


class DiagramView(QtWidgets.QGraphicsView):
    def wheelEvent(self,event):
        if event.modifiers()&QtCore.Qt.ControlModifier:
            factor=1.2 if event.angleDelta().y()>0 else 1/1.2
            self.scale(factor,factor);event.accept()
        else:super().wheelEvent(event)


class ElectricalEditor(QtWidgets.QDialog):
    def __init__(self,obj):
        super().__init__(Gui.getMainWindow(),QtCore.Qt.Window)
        self.obj=obj;self.model=read_model(obj);self.selected=None;self.renderers=[]
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose);self.setWindowTitle('CESS - Eletrica - '+self.model['metadata']['title'])
        self.resize(1280,850);layout=QtWidgets.QVBoxLayout(self);actions=QtWidgets.QHBoxLayout()
        for label,handler in [('Selecionar / mover',self.select_mode),('Fio (2 pontos)',self.wire_mode),('Texto',self.note_mode),
                              ('Girar 90',self.rotate_selected),('Remover',self.remove_selected),('Desfazer',self.undo),
                              ('Prancha / carimbo',self.configure),('Ajustar vista',self.fit),('Salvar FCStd',self.save),('Exportar',self.export)]:
            button=QtWidgets.QPushButton(label);button.clicked.connect(handler);actions.addWidget(button)
        layout.addLayout(actions);splitter=QtWidgets.QSplitter();layout.addWidget(splitter,1)
        left=QtWidgets.QWidget();panel=QtWidgets.QVBoxLayout(left);left.setMinimumWidth(260);left.setMaximumWidth(330)
        panel.addWidget(QtWidgets.QLabel('BIBLIOTECA DE SIMBOLOS'))
        search=QtWidgets.QLineEdit();search.setPlaceholderText('Filtrar simbolos...');panel.addWidget(search)
        self.library=QtWidgets.QListWidget();self.library.setObjectName('CESS_ElectricalLibrary')
        for kind,spec in CATALOG.items():
            item=QtWidgets.QListWidgetItem(spec['category']+' - '+spec['label']);item.setData(QtCore.Qt.UserRole,kind)
            self.library.addItem(item)
        self.library.itemClicked.connect(self.choose_symbol);panel.addWidget(self.library,1)
        search.textChanged.connect(lambda value:[self.library.item(i).setHidden(value.lower() not in self.library.item(i).text().lower()) for i in range(self.library.count())])
        panel.addWidget(QtWidgets.QLabel('PROPRIEDADES DA SELECAO'))
        form=QtWidgets.QFormLayout();self.selection_label=QtWidgets.QLabel('Nenhum item');form.addRow('Item',self.selection_label)
        self.tag=QtWidgets.QLineEdit();self.tag.setMaxLength(24);form.addRow('Tag / numero fio',self.tag)
        self.description=QtWidgets.QPlainTextEdit();self.description.setMaximumHeight(65);form.addRow('Descricao / texto',self.description)
        self.x=QtWidgets.QDoubleSpinBox();self.y=QtWidgets.QDoubleSpinBox()
        for spin in (self.x,self.y):spin.setRange(0,1500);spin.setDecimals(1);spin.setSuffix(' mm')
        form.addRow('X',self.x);form.addRow('Y',self.y)
        self.rotation=QtWidgets.QComboBox();self.rotation.addItems(['0','90','180','270']);form.addRow('Rotacao',self.rotation)
        self.size=QtWidgets.QDoubleSpinBox();self.size.setRange(1.5,10);self.size.setValue(3);form.addRow('Altura do texto',self.size)
        self.apply_button=QtWidgets.QPushButton('Aplicar propriedades');self.apply_button.clicked.connect(self.apply_selection)
        panel.addLayout(form);panel.addWidget(self.apply_button);splitter.addWidget(left)
        self.scene=DiagramScene(self);self.view=DiagramView(self.scene);self.view.setObjectName('CESS_ElectricalCanvas')
        self.view.setRenderHints(QtGui.QPainter.Antialiasing|QtGui.QPainter.TextAntialiasing)
        self.view.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag);splitter.addWidget(self.view);splitter.setStretchFactor(1,1)
        self.status=QtWidgets.QLabel();self.status.setWordWrap(True);layout.addWidget(self.status)
        self.scene.selectionChanged.connect(self.selection_changed)
        self.shortcuts=[]
        for key,handler in [('Escape',self.select_mode),('Delete',self.remove_selected),('Ctrl+Z',self.undo),('Ctrl+S',self.save)]:
            shortcut=QtGui.QShortcut(QtGui.QKeySequence(key),self);shortcut.activated.connect(handler);self.shortcuts.append(shortcut)
        self.refresh();QtCore.QTimer.singleShot(0,self.fit);self.select_mode()

    def message(self,value,error=False):
        self.status.setStyleSheet('color:#a32626' if error else 'color:#24405b');self.status.setText(value)
    def refresh(self):
        self.model=read_model(self.obj);self.scene.blockSignals(True);self.scene.clear();self.scene.preview=None
        self.scene.wire_items={};self.renderers=[]
        renderer=QtSvg.QSvgRenderer(QtCore.QByteArray(render_svg(self.model,contents=False).encode('utf-8')))
        paper=QtSvgWidgets.QGraphicsSvgItem();paper.setSharedRenderer(renderer);self.renderers.append(renderer)
        w,h=dimensions(self.model);rect=paper.boundingRect();paper.setTransform(QtGui.QTransform.fromScale(w/rect.width(),h/rect.height()))
        self.scene.addItem(paper);paper.setZValue(-10)
        x0,y0,x1,y1=drawing_bounds(self.model);grid=self.model['grid'];path=QtGui.QPainterPath()
        x=x0
        while x<=x1:path.moveTo(x,y0);path.lineTo(x,y1);x+=grid
        y=y0
        while y<=y1:path.moveTo(x0,y);path.lineTo(x1,y);y+=grid
        self.scene.addPath(path,QtGui.QPen(QtGui.QColor('#e5edf5'),.08)).setZValue(-5)
        for wire in self.model['wires']:
            item=WireItem(painter_path(wire_points(self.model,wire)));item.setPen(QtGui.QPen(QtGui.QColor(wire['color']),.35));self.scene.addItem(item)
            item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable);item.setData(0,'wire');item.setData(1,wire['id'])
            self.scene.wire_items[wire['id']]=item
            if wire['label']:
                p=wire_points(self.model,wire)[0];label=self.scene.addSimpleText(wire['label'])
                label.setScale(.25);label.setPos(p[0]+1,p[1]+1)
        for symbol in self.model['symbols']:self.scene.addItem(SymbolItem(symbol,self))
        for note in self.model['notes']:
            item=self.scene.addText(note['text']);font=QtGui.QFont('Arial');font.setPixelSize(10);item.setFont(font)
            item.setScale(note['size']/10);item.setPos(note['x'],note['y']);item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
            item.setData(0,'note');item.setData(1,note['id'])
        self.scene.setSceneRect(-5,-5,w+10,h+10);self.scene.blockSignals(False)
        self.selected=None;self.selection_changed()
    def fit(self):self.view.fitInView(self.scene.sceneRect(),QtCore.Qt.KeepAspectRatio)
    def commit(self,model,transaction='Editar diagrama eletrico'):
        try:
            apply_model(self.obj,model,transaction);self.refresh();self.message('Alteracao aplicada ao documento. Salve FCStd para guardar o projeto.')
        except Exception as error:self.refresh();self.message(str(error),True)
    def select_mode(self):self.scene.cancel()
    def wire_mode(self):
        self.scene.cancel();self.scene.mode='wire';self.message('Fio ortogonal: clique no terminal inicial e depois no final. Cruzamentos so recebem ponto quando voce inserir uma juncao.')
    def note_mode(self):self.scene.cancel();self.scene.mode='note';self.message('Clique na prancha para inserir texto.')
    def choose_symbol(self,item):
        self.scene.cancel();self.scene.mode='symbol';self.scene.kind=item.data(QtCore.Qt.UserRole)
        self.message('Clique na prancha para inserir '+CATALOG[self.scene.kind]['label']+'. Esc volta a selecionar.')
    def selection_changed(self):
        items=[i for i in self.scene.selectedItems() if i.data(1)]
        self.selected=(items[0].data(0),items[0].data(1)) if len(items)==1 else None
        self.apply_button.setEnabled(self.selected is not None)
        if self.selected is None:self.selection_label.setText('Nenhum item');return
        kind,item_id=self.selected;key={'symbol':'symbols','wire':'wires','note':'notes'}[kind]
        item=next(i for i in self.model[key] if i['id']==item_id);self.selection_label.setText(item_id)
        self.tag.setText(item.get('tag',item.get('label','')));self.tag.setEnabled(kind!='note')
        self.description.setPlainText(item.get('description',item.get('text','')));self.description.setEnabled(kind!='wire')
        for spin in (self.x,self.y):spin.setEnabled(kind!='wire')
        self.x.setValue(item.get('x',0));self.y.setValue(item.get('y',0))
        self.rotation.setEnabled(kind=='symbol');self.rotation.setCurrentText(str(int(item.get('rotation',0))))
        self.size.setEnabled(kind=='note');self.size.setValue(item.get('size',3))
    def apply_selection(self):
        if self.selected is None:return
        kind,item_id=self.selected;model=deepcopy(self.model);key={'symbol':'symbols','wire':'wires','note':'notes'}[kind]
        item=next(i for i in model[key] if i['id']==item_id)
        if kind=='symbol':item.update(tag=self.tag.text(),description=self.description.toPlainText(),x=self.x.value(),y=self.y.value(),rotation=int(self.rotation.currentText()))
        elif kind=='wire':item['label']=self.tag.text()
        else:item.update(text=self.description.toPlainText(),x=self.x.value(),y=self.y.value(),size=self.size.value())
        self.commit(model,'Editar propriedades eletricas')
    def rotate_selected(self):
        if self.selected and self.selected[0]=='symbol':self.rotation.setCurrentText(str((int(self.rotation.currentText())+90)%360));self.apply_selection()
    def remove_selected(self):
        selected=[i.data(1) for i in self.scene.selectedItems() if i.data(1)]
        if not selected:return
        model=self.model
        for item_id in selected:model=remove_item(model,item_id)
        self.commit(model,'Remover selecao eletrica')
    def undo(self):
        try:self.obj.Document.undo();self.obj.Document.recompute();self.refresh()
        except Exception as error:self.message(str(error),True)
    def configure(self):
        dialog=SheetDialog(self.model)
        if dialog.exec_()==QtWidgets.QDialog.Accepted:self.commit(dialog.result_model,'Editar prancha e carimbo')
    def save(self):
        try:
            root=models_root();root.mkdir(parents=True,exist_ok=True);current=self.obj.Document.FileName
            if not current:current,_=QtWidgets.QFileDialog.getSaveFileName(self,'Salvar projeto FreeCAD',str(root/(self.obj.Document.Name+'.FCStd')),'FreeCAD (*.FCStd)')
            if not current:return
            if not Path(current).suffix:current+='.FCStd'
            path=safe_path(root,current,'.FCStd');path.parent.mkdir(parents=True,exist_ok=True)
            self.obj.Document.recompute();self.obj.Document.saveAs(str(path));self.message('Projeto salvo: '+str(path))
        except Exception as error:self.message(str(error),True)
    def export(self):
        try:
            root=models_root();root.mkdir(parents=True,exist_ok=True)
            filename,kind=QtWidgets.QFileDialog.getSaveFileName(self,'Exportar prancha',str(root/'prancha_eletrica.pdf'),
                'PDF (*.pdf);;SVG (*.svg);;PNG (*.png);;Desenho JSON (*.json)')
            if not filename:return
            if not Path(filename).suffix:filename+='.'+('json' if 'JSON' in kind else ('svg' if 'SVG' in kind else ('png' if 'PNG' in kind else 'pdf')))
            ext=Path(filename).suffix.lower()
            if ext not in ('.svg','.pdf','.png','.json'):raise ValueError('Formato de exportacao invalido.')
            path=safe_path(root,filename,ext);path.parent.mkdir(parents=True,exist_ok=True)
            result=export_sheet(self.obj,path);self.message('Prancha exportada: '+result['path'])
        except Exception as error:self.message(str(error),True)


def open_editor(obj):
    for editor in list(_editors):
        try:
            if editor.obj==obj:editor.refresh();editor.show();editor.raise_();return editor
        except RuntimeError:_editors.remove(editor)
    editor=ElectricalEditor(obj);_editors.append(editor);editor.show();return editor


def selected_sheet():
    selection=[obj for obj in Gui.Selection.getSelection() if is_sheet(obj)]
    if len(selection)==1:return selection[0]
    candidates=[obj for obj in App.ActiveDocument.Objects if is_sheet(obj)] if App.ActiveDocument else []
    if not candidates:raise ValueError('Crie uma prancha eletrica primeiro.')
    if len(candidates)==1:return candidates[0]
    names=[obj.Name+' - '+obj.Title for obj in candidates]
    value,ok=QtWidgets.QInputDialog.getItem(Gui.getMainWindow(),'Prancha eletrica','Escolha a prancha:',names,0,False)
    if not ok:return None
    return candidates[names.index(value)]


class ElectricalCommand:
    def __init__(self,action,label):self.action,self.label=action,label
    def GetResources(self):return dict(MenuText=self.label,ToolTip=self.label,Pixmap=str(Path(__file__).parent/'icons/electrical.svg'))
    def IsActive(self):return True
    def Activated(self):
        try:
            if self.action in ('new','example'):
                if self.action=='new':
                    dialog=SheetDialog()
                    if dialog.exec_()!=QtWidgets.QDialog.Accepted:return
                    model=dialog.result_model
                else:
                    from cess_gui.electrical_examples import start_stop_example
                    model=start_stop_example()
                doc=App.ActiveDocument or App.newDocument('ProjetoEletrico');name='PranchaEletrica';i=1
                while doc.getObject(name):i+=1;name='PranchaEletrica'+str(i)
                obj=create_sheet(doc,name,model)
                try:Gui.activeDocument().getObject(obj.PageName).show()
                except Exception:pass
                open_editor(obj)
            else:
                obj=selected_sheet()
                if obj:
                    editor=open_editor(obj)
                    if self.action=='export':editor.export()
        except Exception as error:QtWidgets.QMessageBox.information(Gui.getMainWindow(),'CESS - Eletrica',str(error))


def install():
    window=Gui.getMainWindow();toolbar=window.findChild(QtWidgets.QToolBar,'CESS_ElectricalToolbar')
    fresh=toolbar is None
    if fresh:
        toolbar=QtWidgets.QToolBar('CESS - Eletrica',window);toolbar.setObjectName('CESS_ElectricalToolbar')
        toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon);toolbar.setIconSize(QtCore.QSize(24,24))
    for action,label in [('new','Nova prancha eletrica'),('edit','Editar diagrama'),('export','Exportar prancha'),('example','Exemplo de comando')]:
        name='CESS_Electrical_'+action
        if any(a.objectName()==name for a in toolbar.actions()):continue
        command=ElectricalCommand(action,label);Gui.addCommand(name,command);_commands.append(command)
        button=toolbar.addAction(QtGui.QIcon(command.GetResources()['Pixmap']),label);button.setObjectName(name)
        button.triggered.connect(lambda checked=False,name=name:Gui.runCommand(name,0))
    if fresh:window.addToolBarBreak(QtCore.Qt.TopToolBarArea);window.addToolBar(QtCore.Qt.TopToolBarArea,toolbar)
    toolbar.show();return toolbar
