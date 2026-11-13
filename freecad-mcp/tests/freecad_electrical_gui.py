"""Real Qt editor, TechDraw page, all paper sizes and export/persistence checks."""
import json,time
from pathlib import Path
from copy import deepcopy
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore,QtGui
try:
    from PySide6 import QtTest
except ImportError:
    from PySide2 import QtTest
from cess_gui.electrical_editor import ElectricalEditor,SheetDialog,install,QtWidgets
from cess_gui.electrical_project import create_sheet,read_model,apply_model,export_sheet
from cess_gui.electrical_model import new_drawing,dimensions,wire_points
from cess_gui.electrical_examples import start_stop_example


def run(project):
    project=Path(project);folder=project.parent/'modelos'/('eletrica_validacao_'+str(time.time_ns()));folder.mkdir(parents=True)
    report={'passed':False,'folder':str(folder),'papers':[]}
    toolbar=install();assert len(toolbar.actions())==4 and len(install().actions())==4
    doc=App.newDocument('TesteFormatosEletricos')
    for paper in ('A0','A1','A2','A3','A4'):
      for orientation in ('portrait','landscape'):
        model=new_drawing(paper,orientation,{'company':'SENAI / CESS','title':'Prancha '+paper})
        obj=create_sheet(doc,paper+'_'+orientation,model)
        template=doc.getObject(obj.TemplateName);w,h=dimensions(model)
        assert not obj.LastError
        assert abs(template.Width.Value-w)<.01 and abs(template.Height.Value-h)<.01,(paper,template.Width,template.Height)
        pdf=export_sheet(obj,folder/(paper+'_'+orientation+'.pdf'))
        assert pdf['bytes']>1000
        report['papers'].append(dict(paper=paper,orientation=orientation,size_mm=[w,h],pdf=pdf['path']))
    App.closeDocument(doc.Name)
    doc=App.newDocument('TesteEditorEletrico');obj=create_sheet(doc,'Prancha')
    editor=ElectricalEditor(obj);editor.setObjectName('CESS_ElectricalTestEditor');editor.show()
    editor.raise_();editor.activateWindow();QtWidgets.QApplication.setActiveWindow(editor)
    QtTest.QTest.qWaitForWindowExposed(editor,5000);QtWidgets.QApplication.processEvents();editor.fit()
    modal=QtWidgets.QApplication.activeModalWidget()
    diagnostic={'modal':modal.windowTitle() if modal else None,'editor_enabled':editor.isEnabled(),
                'library_enabled':editor.library.isEnabled(),'visible':editor.library.isVisible()}
    (project/'.runtime/electrical-ui-diagnostic.json').write_text(json.dumps(diagnostic,indent=2),encoding='utf-8')
    def mouse_click(widget,pos):
        QtTest.QTest.mouseClick(widget,QtCore.Qt.LeftButton,QtCore.Qt.NoModifier,pos)
        QtWidgets.QApplication.processEvents()
    def palette(kind):
        item=next(editor.library.item(i) for i in range(editor.library.count()) if editor.library.item(i).data(QtCore.Qt.UserRole)==kind)
        editor.library.scrollToItem(item);QtWidgets.QApplication.processEvents()
        editor.library.setFocus()
        mouse_click(editor.library.viewport(),editor.library.visualItemRect(item).center())
        QtWidgets.QApplication.processEvents()
        diagnostic.update(row=editor.library.currentRow(),item_kind=item.data(QtCore.Qt.UserRole),
                          rect=str(editor.library.visualItemRect(item)),scene_mode=editor.scene.mode,scene_kind=editor.scene.kind,
                          active=editor.isActiveWindow())
        editor.grab().save(str(project/'.runtime/electrical-editor-debug.png'))
        (project/'.runtime/electrical-ui-diagnostic.json').write_text(json.dumps(diagnostic,indent=2),encoding='utf-8')
    def click(x,y):
        p=editor.view.mapFromScene(QtCore.QPointF(x,y))
        mouse_click(editor.view.viewport(),p)
        QtWidgets.QApplication.processEvents()
    palette('contact_no');assert editor.scene.kind=='contact_no';click(80,80)
    assert obj.SymbolCount==1
    palette('coil');click(80,140);assert obj.SymbolCount==2
    next(b for b in editor.findChildren(QtWidgets.QPushButton) if b.text()=='Fio (2 pontos)').click()
    click(80,90);click(80,130);assert obj.WireCount==1
    editor.select_mode()
    symbol=next(i for i in editor.scene.items() if i.data(0)=='symbol' and i.data(1)=='C1')
    symbol.setSelected(True);editor.selection_changed();editor.x.setValue(100);editor.apply_button.click()
    actual=read_model(obj);assert actual['symbols'][0]['x']==100
    assert wire_points(actual,actual['wires'][0])[0]==[100,90]
    editor.undo();assert read_model(obj)['symbols'][0]['x']==80
    palette('timer_on_changeover');click(160,80);assert obj.SymbolCount==3
    palette('limit_no_nc');click(160,140);assert obj.SymbolCount==4
    next(b for b in editor.findChildren(QtWidgets.QPushButton) if b.text()=='Fio (2 pontos)').click()
    click(160,70);click(156,130);assert obj.WireCount==2
    assert editor.library.count()==77
    editor.grab().save(str(folder/'editor_eletrica.png'))
    dialog=SheetDialog(read_model(obj));dialog.paper.setCurrentText('A4');dialog.orientation.setCurrentIndex(1)
    dialog.fields['title'].setText('Projeto de comando');dialog.apply()
    assert dialog.result_model['paper']=='A4' and dialog.result_model['metadata']['title']=='Projeto de comando'
    editor.close();dialog.deleteLater();App.closeDocument(doc.Name)
    doc=App.newDocument('ExemploComandoEletrico');obj=create_sheet(doc,'Comando',start_stop_example())
    for extension in ('.svg','.pdf','.png','.json'):export_sheet(obj,folder/('exemplo_comando'+extension))
    path=folder/'exemplo_comando.FCStd';doc.recompute();doc.saveAs(str(path));App.closeDocument(doc.Name)
    doc=App.openDocument(str(path));doc.recompute();obj=doc.getObject('Comando')
    assert obj.SymbolCount==14 and obj.WireCount==15 and not obj.LastError
    assert doc.getObject(obj.PageName).Template==doc.getObject(obj.TemplateName)
    original=read_model(obj);edited=deepcopy(original);edited['metadata']['author']='Responsavel editavel'
    apply_model(obj,edited);assert read_model(obj)['metadata']['author']=='Responsavel editavel'
    doc.undo();doc.recompute();assert read_model(obj)==original
    Gui.activeDocument().getObject(obj.PageName).show()
    report.update(passed=True,toolbar=True,mouse_insert_symbols=True,mouse_draw_wire=True,
                  library_count=77,new_changeover_and_combined_contacts=True,
                  edit_move_relinks_wire=True,undo=True,carimbo_editable=True,fcstd_reopen=True,
                  example_fcstd=str(path),example_svg=str(folder/'exemplo_comando.svg'),
                  example_png=str(folder/'exemplo_comando.png'),editor_png=str(folder/'editor_eletrica.png'))
    (project/'electrical-gui-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report
