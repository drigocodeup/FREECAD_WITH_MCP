"""Trusted smoke test executed inside a real FreeCAD Qt session."""
import json
from pathlib import Path
import time
import FreeCAD as App
import FreeCADGui as Gui
import Part
import Mesh
from cess_gui.toolbar import install
from cess_gui.generator_dialog import GeneratorDialog, COMMANDS


def run(project):
    project = Path(project)
    install()
    from PySide import QtGui
    try:
        from PySide import QtWidgets
    except ImportError:
        QtWidgets = QtGui
    toolbar = Gui.getMainWindow().findChild(QtWidgets.QToolBar,'CESS_GeneratorsToolbar')
    assert {a.objectName() for a in toolbar.actions()} == set(COMMANDS)
    assert len(toolbar.actions()) == len(COMMANDS)
    folder = project.parent / 'modelos' / ('geradores_'+str(int(time.time())))
    folder.mkdir(parents=True)
    report = {'passed':False,'toolbar':[a.text() for a in toolbar.actions()],'models':{}}
    for kind in ['gear','box','letters','numbers','organizer']:
        doc = App.newDocument('CESS_'+kind)
        dialog = GeneratorDialog(kind)
        assert len(dialog.widgets) >= 5
        dialog.create_button.click()  # Real Qt button signal -> validation -> CAD handler.
        assert dialog.result_objects is not None,dialog.feedback.text()
        result = dialog.result_objects
        objects = [o for o in result['objects'] if not o.Shape.isNull()]
        assert objects and all(o.Shape.isValid() and o.Shape.Solids for o in objects)
        Gui.Selection.clearSelection()
        view = Gui.getDocument(doc.Name).activeView()
        view.viewAxonometric()
        view.fitAll()
        path = folder / kind
        doc.saveAs(str(path.with_suffix('.FCStd')))
        Gui.getDocument(doc.Name).Modified = False
        Part.export(objects,str(path.with_suffix('.step')))
        Mesh.export(objects,str(path.with_suffix('.stl')))
        view.saveImage(str(path.with_suffix('.png')),1400,1000,'White')
        row = {'document':doc.Name,'parameters':result['parameters'].Name,
               'parts':[{'name':o.Name,'label':o.Label,'solids':len(o.Shape.Solids),
                         'valid':o.Shape.isValid(),'volume_mm3':o.Shape.Volume} for o in objects],
               'files':{ext:str(path.with_suffix('.'+ext)) for ext in ['FCStd','step','stl','png']}}
        report['models'][kind] = row
        dialog.deleteLater()
        print('CESS GUI OK: '+kind,flush=True)
    # Invalid parameters must show an error, leave the dialog open and create no objects.
    bad = GeneratorDialog('box')
    count = len(App.ActiveDocument.Objects)
    bad.widgets['floor'].setValue(50)
    bad.create_button.click()
    assert bad.result_objects is None and bad.feedback.text() and len(App.ActiveDocument.Objects) == count
    bad.deleteLater()
    report['invalid_dialog_rejected'] = True
    report['passed'] = True
    (project / '.runtime/generators-gui-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report
