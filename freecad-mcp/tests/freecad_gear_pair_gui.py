"""Trusted Qt test run on the main FreeCAD GUI thread."""
import json
from pathlib import Path
import FreeCAD as App
import FreeCADGui as Gui
from cess_gui.generator_dialog import GeneratorDialog,install


def run(project):
    project = Path(project)
    toolbar = install()
    assert any(a.objectName()=='CESS_ConjuntoEngrenagens' for a in toolbar.actions())
    assert len(install().actions())==len(toolbar.actions())
    doc = App.newDocument('TesteJanelaConjunto')
    dialog = GeneratorDialog('gear_pair')
    assert dialog.create_button.isEnabled()
    assert '20/40' in dialog.summary.text()
    dialog.widgets['ratio'].setText('1:2')
    assert '40/20' in dialog.summary.text() and 'Aumento' in dialog.summary.text()
    dialog.widgets['ratio'].setText('100:1')
    assert not dialog.create_button.isEnabled() and not doc.Objects
    dialog.widgets['ratio'].setText('2:1')
    dialog.create_button.click()
    assert dialog.result_objects is not None,dialog.feedback.text()
    result = dialog.result_objects
    assert len(result['objects'])==6
    assert all(not o.LastError and o.Shape.isValid() and len(o.Shape.Solids)==1 for o in result['objects'])
    info = {'passed':True,'toolbar_command':'CESS_ConjuntoEngrenagens','input_teeth':result['parameters'].InputTeeth,
            'output_teeth':result['parameters'].OutputTeeth,'center_distance_mm':result['parameters'].CenterDistance.Value,
            'parts':[o.Name for o in result['objects']],'invalid_ratio_rejected':True}
    (project/'gear-pair-gui-validation.json').write_text(json.dumps(info,indent=2),encoding='utf-8')
    App.closeDocument(doc.Name)  # Only this test's unsaved document.
    dialog.deleteLater()
    return info
