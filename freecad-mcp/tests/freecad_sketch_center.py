"""Real Sketcher solver regression, executed in the graphical FreeCAD process."""
import json,time
from pathlib import Path
import FreeCAD as App,FreeCADGui as Gui,Part,Sketcher
from PySide import QtCore
from cess_gui.sketch_center import sketch_rectangles,center_sketch_rectangles

def rectangle(sketch,x,y,size):
    start=sketch.GeometryCount
    points=[(x,y),(x+size,y),(x+size,y+size),(x,y+size)]
    for i in range(4):
        a,b=points[i],points[(i+1)%4]
        sketch.addGeometry(Part.LineSegment(App.Vector(*a,0),App.Vector(*b,0)),False)
    for i in range(4):
        sketch.addConstraint(Sketcher.Constraint('Coincident',start+i,2,start+(i+1)%4,1))
        sketch.addConstraint(Sketcher.Constraint('Horizontal' if i%2==0 else 'Vertical',start+i))
    sketch.addConstraint(Sketcher.Constraint('Distance',start,size))
    sketch.addConstraint(Sketcher.Constraint('Distance',start+1,size))
    center=sketch.addGeometry(Part.Point(App.Vector(x+size/2,y+size/2,0)),True)
    sketch.addConstraint(Sketcher.Constraint('DistanceX',start,1,center,1,size/2))
    sketch.addConstraint(Sketcher.Constraint('DistanceY',start,1,center,1,size/2))
    return list(range(start,start+4))

def run(project):
    project=Path(project);doc=App.newDocument('TesteCentralizarSketch_'+str(time.time_ns()));doc.UndoMode=1
    sketch=doc.addObject('Sketcher::SketchObject','Sketch')
    outer=rectangle(sketch,20,20,50);inner=rectangle(sketch,20,30,40)
    sketch.addConstraint(Sketcher.Constraint('DistanceX',outer[0],1,20))
    sketch.addConstraint(Sketcher.Constraint('DistanceY',outer[0],1,20))
    doc.recompute();assert sketch.solve()==0
    before=sketch_rectangles(sketch);constraints=sketch.ConstraintCount
    result=center_sketch_rectangles(sketch,inner,outer)
    after=sketch_rectangles(sketch)
    assert all(abs(a-b)<1e-6 for a,b in zip(after[0]['center'],after[1]['center']))
    assert after[0]['size']==(40,40) and after[1]['size']==(50,50)
    assert sketch.ConstraintCount==constraints
    doc.undo();doc.recompute();assert sketch_rectangles(sketch)==before
    doc.redo();doc.recompute();assert sketch_rectangles(sketch)==after
    doc.undo();doc.recompute()
    for axis in ('X','Y'):
        center_sketch_rectangles(sketch,inner,outer,axis)
        partial=sketch_rectangles(sketch)
        i=0 if axis=='X' else 1;j=1-i
        assert abs(partial[0]['center'][i]-partial[1]['center'][i])<1e-6
        assert abs(partial[0]['center'][j]-before[0]['center'][j])<1e-6
        doc.undo();doc.recompute()
    # A positional lock must not be silently removed to achieve centering.
    lock=sketch.addConstraint(Sketcher.Constraint('DistanceX',inner[0],1,20));doc.recompute()
    locked=sketch_rectangles(sketch);count=sketch.ConstraintCount
    try:center_sketch_rectangles(sketch,inner,outer)
    except (ValueError,RuntimeError):pass
    else:raise AssertionError('Position-locked rectangle should not move')
    assert sketch_rectangles(sketch)==locked and sketch.ConstraintCount==count
    sketch.delConstraint(lock);doc.recompute()
    # Exercise the same command path as the toolbar while Sketcher is in edit mode.
    from cess_gui.toolbar import SketchCenterDialog,QtWidgets,install
    toolbar=install()
    Gui.activeDocument().setEdit(sketch.Name);Gui.Selection.clearSelection()
    Gui.Selection.addSelection(sketch,'Edge1');Gui.Selection.addSelection(sketch,'Edge6')
    outcome={}
    def apply_dialog():
        dialog=QtWidgets.QApplication.activeModalWidget()
        if not isinstance(dialog,SketchCenterDialog):
            outcome['error']='Unexpected modal: '+str(type(dialog))
            if dialog and dialog.windowTitle().startswith('CESS'):dialog.reject()
            return
        dialog.apply();outcome['accepted']=dialog.result()==QtWidgets.QDialog.Accepted
        if not outcome['accepted']:outcome['error']=dialog.feedback.text();dialog.reject()
    QtCore.QTimer.singleShot(150,apply_dialog);toolbar.actions()[0].trigger()
    assert outcome.get('accepted'),outcome
    Gui.activeDocument().resetEdit();Gui.activeDocument().activeView().viewTop();Gui.activeDocument().activeView().fitAll()
    folder=project.parent/'modelos/centralizar_sketch';folder.mkdir(exist_ok=True)
    path=folder/('retangulos_50_40_'+str(time.time_ns())+'.FCStd');doc.saveAs(str(path))
    Gui.activeDocument().activeView().saveImage(str(path.with_suffix('.png')),1200,850,'White')
    report=dict(passed=True,rectangles_mm=[50,40],equal_margins_mm=5,dimensions_preserved=True,
                reference_fixed=True,undo_redo=True,positional_lock_rollback=True,in_edit_command=True,partial_axes=True,
                constraints_preserved=sketch.ConstraintCount==constraints,translation=result,fcstd=str(path))
    (project/'sketch-center-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    App.closeDocument(doc.Name)
    return report
