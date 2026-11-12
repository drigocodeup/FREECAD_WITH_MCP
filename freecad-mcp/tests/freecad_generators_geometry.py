"""Run with FreeCAD's embedded python.exe, not system pytest. No mocks."""
import json
import math
from pathlib import Path
import sys
import time
import FreeCAD as App
import Part
import MeshPart

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT))
from cess_gui.generators import build_shapes, create_generator


def near(a,b):
    assert math.isclose(a,b,rel_tol=1e-7,abs_tol=1e-6),(a,b)


def export_roundtrip(shapes, output, name):
    combined = Part.makeCompound([solid for shape in shapes.values() for solid in shape.Solids])
    path = output / (name+'.step')
    combined.exportStep(str(path))
    loaded = Part.Shape()
    loaded.read(str(path))
    assert loaded.isValid() and len(loaded.Solids)==len(combined.Solids)
    near(loaded.Volume,combined.Volume)
    mesh = MeshPart.meshFromShape(Shape=combined,LinearDeflection=.05,AngularDeflection=.2,Relative=False)
    assert mesh.isSolid() and math.isclose(mesh.Volume,combined.Volume,rel_tol=.02)
    return {'step_solids':len(loaded.Solids),'step_volume_mm3':loaded.Volume,'stl_closed':mesh.isSolid()}


def geometry_checks(output):
    evidence = {}
    a = build_shapes('gear',{})['Engrenagem']
    b = build_shapes('gear',{'bore':0})['Engrenagem']
    near(b.Volume-a.Volume,math.pi*4**2*10)
    near(a.BoundBox.ZLength,10)
    assert not a.isInside(App.Vector(0,0,5),1e-6,True)
    assert a.isInside(App.Vector(10,0,5),1e-6,True)
    evidence['gear'] = {'valid':a.isValid(),'solids':len(a.Solids),'bore_volume_removed':b.Volume-a.Volume}
    shapes = build_shapes('box',{})
    base,lid = shapes['Base'],shapes['Tampa']
    expected = 120*80*40 - 116*76*38
    near(base.Volume,expected)
    assert not base.isInside(App.Vector(60,40,10),1e-6,True)
    assert base.isInside(App.Vector(60,40,1),1e-6,True)
    assembled = lid.copy()
    assembled.translate(App.Vector(-135,0,35))
    near(base.common(assembled).Volume,0)
    near(assembled.BoundBox.ZMax,42)
    evidence['box'] = {'base_volume':base.Volume,'expected':expected,'lid_assembled_intersection_mm3':base.common(assembled).Volume}
    org = build_shapes('organizer',{})['Organizador']
    cell_l,cell_w = (116-4)/3,(76-2)/2
    expected = 120*80*40 - 6*cell_l*cell_w*38
    near(org.Volume,expected)
    for row in range(2):
        for col in range(3):
            assert not org.isInside(App.Vector(2+col*(cell_l+2)+cell_l/2,2+row*(cell_w+2)+cell_w/2,10),1e-6,True)
    assert org.isInside(App.Vector(2+cell_l+1,20,10),1e-6,True)
    evidence['organizer'] = {'cells_checked':6,'volume':org.Volume,'expected':expected,'solids':len(org.Solids)}
    for kind,text in [('letters','AB'),('numbers','08'),('letters','CESS'),('numbers','123')]:
        result = build_shapes(kind,{'text':text})
        body,front = result['Corpos'],result['Frentes']
        # Optimal bounds avoid BSpline control-point overestimation in ordinary BoundBox.
        near(body.optimalBoundingBox().ZLength,20)
        near(front.optimalBoundingBox().ZLength,1.5)
        # Lower slice includes the full rear plate; upper slice contains only walls.
        bb = body.BoundBox
        low = body.common(Part.makeBox(bb.XLength+2,bb.YLength+2,.5,App.Vector(bb.XMin-1,bb.YMin-1,.5)))
        high = body.common(Part.makeBox(bb.XLength+2,bb.YLength+2,.5,App.Vector(bb.XMin-1,bb.YMin-1,10)))
        assert 0 < high.Volume < low.Volume * .9
        assert front.BoundBox.YMax < body.BoundBox.YMin
        evidence[kind] = {'text':text,'lower_slice_volume':low.Volume,'upper_slice_volume':high.Volume,
                          'body_solids':len(body.Solids),'front_solids':len(front.Solids)}
        evidence[kind+'_'+text+'_export'] = export_roundtrip(result,output,kind+'_'+text)
    # Exercise curved/double-counter characters, a full capital alphabet and all digits.
    for kind,text in [('letters','ABCDEFGHIJKLM'),('letters','NOPQRSTUVWXYZ'),('letters','ÇÁ'),
                      ('numbers','0123456789')]:
        result = build_shapes(kind,{'text':text,'make_front':False})
        assert result['Corpos'].isValid() and result['Corpos'].Solids
        evidence[kind+'_'+text+'_export'] = export_roundtrip(result,output,kind+'_'+text)
        print('GLYPHS OK',text,flush=True)
    evidence['glyphs'] = 'A-Z, ÇÁ, 0-9; AB and 08 with separate fronts'
    return evidence


def parametric_checks(output):
    evidence = {}
    for kind in ['gear','box','letters','numbers','organizer']:
        doc = App.newDocument('Gerador_'+kind)
        doc.UndoMode = 1
        item = create_generator(kind,document=doc,name='Modelo')
        config,objects = item['parameters'],item['objects']
        first = objects[0]
        before = first.Shape.Volume
        changes = {'gear':('Thickness',14),'box':('Length',140),'letters':('Depth',25),
                   'numbers':('Depth',25),'organizer':('Columns',4)}
        prop,value = changes[kind]
        setattr(config,prop,value)
        doc.recompute()
        assert first.LastError == '' and first.Shape.isValid()
        assert abs(before-first.Shape.Volume)>1
        if kind == 'box':
            near(objects[0].Shape.BoundBox.XLength,140)
            near(objects[1].Shape.BoundBox.XLength,140)
            objects[1].Placement.Base = App.Vector(10,0,0)
            config.Width = 90
            doc.recompute()
            near(objects[1].Placement.Base.x,10)
            near(objects[1].Shape.BoundBox.YLength,90)
            config.Wall = 50
            doc.recompute()
            assert first.LastError and first.Shape.isNull()
            config.Wall = 2
            doc.recompute()
            assert not first.LastError and first.Shape.isValid()
        if kind in ('letters','numbers'):
            config.MakeFront = False
            doc.recompute()
            assert objects[1].Shape.isNull()
            config.MakeFront = True
            doc.recompute()
            assert objects[1].Shape.isValid() and objects[1].Shape.Solids
        filename = output / ('Gerador_'+kind+'.FCStd')
        doc.saveAs(str(filename))
        evidence[kind] = {'parameter':prop,'value':value,'before_volume':before,'after_volume':first.Shape.Volume,
                          'file':str(filename),'parameters':config.Name,'output_names':[o.Name for o in objects]}
        config_name = config.Name
        App.closeDocument(doc.Name)
        reopened = App.openDocument(str(filename))
        restored = getattr(reopened.getObject(config_name),prop)
        near(restored.Value if hasattr(restored,'Value') else restored,value)
        reopened.recompute()
        for name in evidence[kind]['output_names']:
            o = reopened.getObject(name)
            assert not o.LastError and o.Shape.isValid() and o.Shape.Solids
        App.closeDocument(reopened.Name)
        print('PARAMETRIC OK',kind,flush=True)
    return evidence


def reload_checks(report):
    for kind,row in report['parametric'].items():
        filename = Path(row['file'])
        if not filename.is_absolute():
            filename = PROJECT.parent / filename
        doc = App.openDocument(str(filename))
        config = doc.getObject(row['parameters'])
        obj = doc.getObject(row['output_names'][0])
        before = obj.Shape.Volume
        prop = row['parameter']
        value = getattr(config,prop)
        number = value.Value if hasattr(value,'Value') else value
        setattr(config,prop,number+1)
        doc.recompute()
        assert not obj.LastError and obj.Shape.isValid() and abs(obj.Shape.Volume-before)>1
        App.closeDocument(doc.Name)
        print('FRESH PROCESS RELOAD OK',kind,flush=True)


if __name__ == '__main__':
    if len(sys.argv)>1 and sys.argv[1]=='reload':
        report_path = Path(sys.argv[2])
        report = json.loads(report_path.read_text(encoding='utf-8'))
        reload_checks(report)
        report['fresh_process_reload'] = True
        report_path.write_text(json.dumps(report,indent=2),encoding='utf-8')
    else:
        stamp = str(int(time.time()))
        output = PROJECT.parent / 'modelos' / ('geradores_testes_'+stamp)
        output.mkdir(parents=True)
        report = {'geometry':geometry_checks(output),'parametric':parametric_checks(output),'passed':True}
        path = PROJECT / 'generators-geometry-validation.json'
        path.write_text(json.dumps(report,indent=2),encoding='utf-8')
        print('REPORT',path,flush=True)
