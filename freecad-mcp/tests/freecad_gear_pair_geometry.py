"""Real OCCT geometry, kinematic samples, housing and parametric persistence."""
import json
from pathlib import Path
import sys
import FreeCAD as App
import Part

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT))
from cess_gui.generators import build_shapes,create_generator
from cess_gui.generator_specs import validate
from cess_gui.gear_sets import gear_pair_layout


def run():
    report = {'passed':False,'cases':[]}
    for ratio in ('2:1','1:2','3:2','23:21'):
        for angle in (0,3,7,13):
            params = validate('gear_pair',dict(ratio=ratio,input_angle=angle,lid_open=False))
            info = gear_pair_layout(params)
            shapes = build_shapes('gear_pair',params)
            assert len(shapes)==6
            assert all(s.isValid() and len(s.Solids)==1 and s.Volume>0 for s in shapes.values())
            pairs = [('EngrenagemEntrada','EngrenagemSaida'),('EngrenagemEntrada','Caixa'),
                     ('EngrenagemSaida','Caixa'),('EngrenagemEntrada','Tampa'),('EngrenagemSaida','Tampa'),
                     ('EixoEntrada','Caixa'),('EixoSaida','Caixa'),('EixoEntrada','Tampa'),('EixoSaida','Tampa'),
                     ('EngrenagemEntrada','EixoEntrada'),('EngrenagemSaida','EixoSaida'),('Caixa','Tampa')]
            intersections = {a+'/'+b:shapes[a].common(shapes[b]).Volume for a,b in pairs}
            assert max(intersections.values())<1e-5,(ratio,angle,intersections)
            report['cases'].append(dict(ratio=ratio,angle=angle,layout=info,intersection_mm3=intersections))
            print('GEAR PAIR OK',ratio,angle,flush=True)
    doc = App.newDocument('PersistenciaConjunto')
    created = create_generator('gear_pair',document=doc,name='Conjunto')
    config = created['parameters']
    assert config.InputTeeth==20 and config.OutputTeeth==40
    config.Ratio = '1:2'
    config.Module = 2.5
    doc.recompute()
    assert config.InputTeeth==40 and config.OutputTeeth==20
    assert abs(config.CenterDistance.Value-75.1)<1e-8
    assert all(not o.LastError and o.Shape.isValid() for o in created['objects'])
    folder = PROJECT.parent/'modelos'/'conjuntos_engrenagens'
    folder.mkdir(parents=True,exist_ok=True)
    path = folder/'persistencia.FCStd'
    doc.saveAs(str(path))
    App.closeDocument(doc.Name)
    doc = App.openDocument(str(path))
    config = doc.getObject('Conjunto_Parametros')
    config.Ratio='2:1'
    doc.recompute()
    assert config.InputTeeth==20 and config.OutputTeeth==40
    assert all(o.Shape.isValid() for o in doc.Objects if hasattr(o,'Shape'))
    report['parametric_edit_and_reopen']=True
    report['passed']=True
    (PROJECT/'gear-pair-geometry-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')


if __name__=='__main__': run()
