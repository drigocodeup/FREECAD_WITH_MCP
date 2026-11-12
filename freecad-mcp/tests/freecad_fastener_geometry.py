"""Real thread/mesh/export tests using FreeCAD's embedded Python."""
import json,math,sys
from pathlib import Path
import FreeCAD as App
import Part,MeshPart
PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT))
from cess_gui.generators import build_shapes,create_generator
from cess_gui.generator_specs import validate


def run():
    report={'passed':False,'cases':[]}
    folder=PROJECT.parent/'modelos'/'parafusos_porcas'
    folder.mkdir(parents=True,exist_ok=True)
    for head in ('allen','sextavada'):
      for left in (False,True):
        p=validate('fastener',dict(head_type=head,left_hand=left))
        parts=build_shapes('fastener',p)
        bolt,nut=parts['Parafuso'],parts['Porca']
        for label,s in parts.items():
            assert s.isValid() and len(s.Solids)==1
            s.check(True)
            mesh=MeshPart.meshFromShape(Shape=s,LinearDeflection=.03,AngularDeflection=.15,Relative=False)
            assert mesh.isSolid(),label
            assert math.isclose(mesh.Volume,s.Volume,rel_tol=.02),(label,mesh.Volume,s.Volume)
            # This verifies the helical faces survive triangulation for printing.
            assert len(s.Faces)>10
        overlaps=[]
        for turns in (0,.25,.6,2):
            placed=nut.copy()
            placed.translate(App.Vector(-(p['head_size']+p['nut_size'])/2-10,0,0))
            placed.rotate(App.Vector(),App.Vector(0,0,1),(-1 if left else 1)*360*turns)
            placed.translate(App.Vector(0,0,p['pitch']*turns))
            overlap=bolt.common(placed).Volume
            assert overlap<1e-5,(head,left,turns,overlap)
            overlaps.append(overlap)
        combined=Part.makeCompound(list(parts.values()))
        path=folder/(head+('_esquerda' if left else '_direita')+'.step')
        combined.exportStep(str(path))
        loaded=Part.Shape();loaded.read(str(path))
        assert loaded.isValid() and len(loaded.Solids)==2
        assert math.isclose(loaded.Volume,combined.Volume,rel_tol=1e-6)
        report['cases'].append(dict(head=head,left_hand=left,thread_faces=len(bolt.Faces),
                                    overlaps_mm3=overlaps,step_solids=len(loaded.Solids)))
        print('FASTENER OK',head,left,flush=True)
    doc=App.newDocument('PersistenciaParafuso')
    result=create_generator('fastener',document=doc,name='Fixador')
    cfg=result['parameters']
    cfg.HeadType='sextavada';cfg.Length=25
    doc.recompute()
    assert all(not o.LastError and o.Shape.isValid() for o in result['objects'])
    path=folder/'persistencia.FCStd'
    doc.saveAs(str(path));App.closeDocument(doc.Name)
    doc=App.openDocument(str(path));cfg=doc.getObject('Fixador_Parametros')
    assert str(cfg.HeadType)=='sextavada'
    cfg.HeadType='allen';cfg.LeftHand=True
    doc.recompute()
    assert all(o.Shape.isValid() and not o.LastError for o in doc.Objects if hasattr(o,'Shape') and hasattr(o,'LastError'))
    report.update(passed=True,parametric_edit_and_reopen=True)
    (PROJECT/'fastener-geometry-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')


def parameter_case():
    p=validate('fastener',dict(diameter=6,pitch=1,length=20,head_size=10,head_height=6,
                              socket_size=5,socket_depth=3,nut_size=10,nut_height=5,clearance=.25))
    parts=build_shapes('fastener',p)
    for shape in parts.values():
        assert shape.isValid() and len(shape.Solids)==1
        shape.check(True)
    nut=parts['Porca'].copy()
    nut.translate(App.Vector(-(p['head_size']+p['nut_size'])/2-10,0,0))
    overlap=parts['Parafuso'].common(nut).Volume
    assert overlap<1e-5
    report=dict(passed=True,parameters=p,assembled_intersection_mm3=overlap,
                volumes_mm3={k:s.Volume for k,s in parts.items()})
    (PROJECT/'fastener-parameters-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('FASTENER CUSTOM DIMENSIONS OK',flush=True)


if __name__=='__main__':
    parameter_case() if '--parameters' in sys.argv else run()
