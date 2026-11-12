"""Run by a trusted macro inside the real FreeCAD GUI, not ordinary pytest."""
import json
from pathlib import Path
import time
import FreeCAD as App
import FreeCADGui as Gui
import Draft
from cess_gui.toolbar import install, center_objects, world_center, CenterDialog


def run(project):
    project = Path(project)
    toolbar = install()
    assert [a.objectName() for a in toolbar.actions()] == ['CESS_Centralizar', 'CESS_Cotas', 'CESS_Texto']
    assert install() is toolbar  # Re-running the macro must not duplicate buttons.
    stamp = str(int(time.time()))
    doc = App.newDocument('DesenhoCESS_' + stamp)
    doc.UndoMode = 1
    outer = Draft.make_rectangle(100, 100, face=False)
    outer.Label = 'Quadrado maior - referencia'
    inner = Draft.make_rectangle(40, 40, placement=App.Placement(App.Vector(75, 60, 0), App.Rotation()), face=False)
    inner.Label = 'Quadrado menor - mover'
    outer.ViewObject.LineColor = (0.18, 0.23, 0.32)
    inner.ViewObject.LineColor = (0.02, 0.42, 0.85)
    outer.ViewObject.LineWidth = inner.ViewObject.LineWidth = 3.0
    doc.recompute()
    initial = inner.Placement.Base
    result = center_objects(inner, outer, 'XY')
    assert (world_center(inner) - world_center(outer)).Length < 1e-6
    assert (inner.Placement.Base - App.Vector(30, 30, 0)).Length < 1e-6
    doc.undo()
    doc.recompute()
    assert (inner.Placement.Base - initial).Length < 1e-6
    doc.redo()
    doc.recompute()
    assert (world_center(inner) - world_center(outer)).Length < 1e-6
    dialog = CenterDialog(inner, outer)
    assert dialog.axes.currentData() == 'XY'
    dialog.swap()
    assert dialog.moving == outer
    dialog.swap()
    dialog.deleteLater()
    Gui.activateWorkbench('DraftWorkbench')
    dimension = Draft.make_linear_dimension(App.Vector(0, 0, 0), App.Vector(100, 0, 0), App.Vector(50, -12, 0))
    dimension.Label = 'Cota horizontal 100 mm'
    dimension.ViewObject.FontSize = 5.0
    dimension.ViewObject.ArrowSizeStart = 2.0
    dimension.ViewObject.ArrowSizeEnd = 2.0
    text = Draft.make_text(['CESS - Centralizar, cotas e texto', 'Quadrados concentricos: margens de 30 mm'],
                           placement=App.Vector(0, -26, 0), height=4)
    doc.recompute()
    assert abs(dimension.Distance.Value - 100) < 1e-6
    assert 'CESS' in text.Text[0]
    Gui.Selection.clearSelection()
    native_commands = {}
    for command in ('CESS_Cotas', 'CESS_Texto'):
        Gui.runCommand(command, 0)
        active = getattr(App, 'activeDraftCommand', None)
        assert active is not None, command + ' did not start its interactive tool'
        native_commands[command] = type(active).__name__
        active.finish()
    # Test a transformed container as well: both centers use world coordinates.
    group = doc.addObject('App::Part', 'GrupoTeste')
    group.Placement = App.Placement(App.Vector(200, 50, 0), App.Rotation(App.Vector(0,0,1), 30))
    local = doc.addObject('Part::Box', 'CaixaLocal')
    local.Length = local.Width = local.Height = 10
    group.addObject(local)
    doc.recompute()
    center_objects(local, outer, 'XY')
    assert abs(world_center(local).x - world_center(outer).x) < 1e-6
    assert abs(world_center(local).y - world_center(outer).y) < 1e-6
    group.Visibility = local.Visibility = False
    view = Gui.getDocument(doc.Name).activeView()
    view.viewTop()
    view.fitAll()
    Gui.Selection.clearSelection()
    Gui.Selection.addSelection(inner)
    Gui.Selection.addSelection(outer)
    models = project.parent / 'modelos'
    models.mkdir(exist_ok=True)
    output = models / ('DesenhoCESS_' + stamp + '.FCStd')
    doc.saveAs(str(output))
    Gui.getDocument(doc.Name).Modified = False
    view.saveImage(str(output.with_suffix('.png')), 1400, 1000, 'White')
    report = {'passed': True, 'toolbar': [a.text() for a in toolbar.actions()],
              'alignment': result, 'undo_redo': True, 'transformed_parent': True,
              'dimension_mm': dimension.Distance.Value, 'text': list(text.Text),
              'document': doc.Name, 'fcstd': str(output), 'png': str(output.with_suffix('.png')),
              'interactive_commands': native_commands}
    (project / '.runtime/gui-smoke-result.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report
