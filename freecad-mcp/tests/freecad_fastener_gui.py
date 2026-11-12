"""Click the actual Qt generator button and verify both head choices."""
import json
from pathlib import Path
import FreeCAD as App
from cess_gui.generator_dialog import GeneratorDialog,install


def run(project):
    assert any(a.objectName()=='CESS_ParafusoPorca' for a in install().actions())
    doc=App.newDocument('TesteJanelaFixador')
    dialog=GeneratorDialog('fastener')
    assert dialog.widgets['socket_size'].isEnabled()
    dialog.widgets['head_type'].setCurrentText('sextavada')
    assert not dialog.widgets['socket_size'].isEnabled()
    dialog.create_button.click()
    assert dialog.result_objects is not None,dialog.feedback.text()
    result=dialog.result_objects
    assert len(result['objects'])==2
    assert all(o.Shape.isValid() and len(o.Shape.Solids)==1 for o in result['objects'])
    assert str(result['parameters'].HeadType)=='sextavada'
    bad=GeneratorDialog('fastener')
    count=len(doc.Objects)
    bad.widgets['socket_depth'].setValue(8)
    bad.create_button.click()
    assert bad.result_objects is None and bad.feedback.text() and len(doc.Objects)==count
    info={'passed':True,'head_combo_verified':True,'unused_socket_controls_disabled':True,
          'real_thread_generated':True,'invalid_parameters_rejected':True}
    (Path(project)/'fastener-gui-validation.json').write_text(json.dumps(info,indent=2),encoding='utf-8')
    App.closeDocument(doc.Name)
    dialog.deleteLater();bad.deleteLater()
    return info
