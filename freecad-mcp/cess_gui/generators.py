"""Real, recomputable Part/OCCT generators; only imported in FreeCAD."""
import sys
import json
from functools import lru_cache
from pathlib import Path
import FreeCAD as App
import Part
from cess_gui.generator_specs import SPECS, validate


def checked(shape, name, detailed=False):
    if shape.isNull() or not shape.isValid() or not shape.Solids or shape.Volume <= 0:
        raise ValueError(f'{name}: nao foi possivel gerar solidos validos.')
    if detailed:
        try:
            shape.check(True)
        except Exception as error:
            raise ValueError(f'{name}: a verificacao geometrica detalhada falhou: {error}') from error
    return shape


def gear(p):
    module_path = str(Path(App.ConfigGet('AppHomePath')) / 'Mod/PartDesign')
    if module_path not in sys.path:
        sys.path.append(module_path)
    from fcgear import involute, fcgear
    builder = fcgear.FCWireBuilder()
    involute.CreateExternalGear(builder, p['module'], p['teeth'], p['pressure_angle'], split=True)
    wire = Part.Wire([curve.toShape() for curve in builder.wire])
    solid = Part.Face(wire).extrude(App.Vector(0, 0, p['thickness']))
    if p['bore']:
        cutter = Part.makeCylinder(p['bore']/2, p['thickness']+2, App.Vector(0,0,-1))
        solid = solid.cut(cutter)
    return {'Engrenagem': solid.removeSplitter()}


def box(p):
    l, w, h, wall, floor = (p[k] for k in ('length','width','height','wall','floor'))
    outer = Part.makeBox(l, w, h)
    cavity = Part.makeBox(l-2*wall, w-2*wall, h, App.Vector(wall, wall, floor))
    base = outer.cut(cavity).removeSplitter()
    clearance, lip = p['clearance'], p['lip_depth']
    guide_l, guide_w = l-2*wall-2*clearance, w-2*wall-2*clearance
    ring = Part.makeBox(guide_l, guide_w, lip, App.Vector(wall+clearance,wall+clearance,0))
    ring = ring.cut(Part.makeBox(guide_l-2*wall,guide_w-2*wall,lip+2,
                                App.Vector(2*wall+clearance,2*wall+clearance,-1)))
    plate = Part.makeBox(l,w,p['lid_thickness'],App.Vector(0,0,lip))
    lid = plate.fuse(ring).removeSplitter()
    lid.translate(App.Vector(l+15,0,0))
    return {'Base': base, 'Tampa': lid}


def gear_pair(p):
    from cess_gui.gear_sets import gear_pair_layout
    layout = gear_pair_layout(p)
    outputs = {}
    for label,teeth,x,angle in [
        ('Entrada',layout['input_teeth'],0,layout['input_angle']),
        ('Saida',layout['output_teeth'],layout['center_distance'],layout['output_angle'])]:
        shape = gear(dict(module=p['module'],teeth=teeth,pressure_angle=p['pressure_angle'],
                          thickness=p['thickness'],bore=layout['bore']))['Engrenagem']
        shape.rotate(App.Vector(),App.Vector(0,0,1),angle)
        shape.translate(App.Vector(x,0,0))
        outputs['Engrenagem'+label] = shape
        outputs['Eixo'+label] = Part.makeCylinder(p['shaft_diameter']/2,
            p['thickness']+2*p['shaft_extension'],App.Vector(x,0,-p['shaft_extension']))
    if p['make_housing']:
        wall,gap,axial = p['housing_wall'],p['housing_clearance'],p['axial_clearance']
        r1,r2 = layout['input_tip_radius'],layout['output_tip_radius']
        xmin,ymin = -r1-gap,-max(r1,r2)-gap
        length,width = layout['center_distance']+r2+gap-xmin,2*(max(r1,r2)+gap)
        bottom = -axial-wall
        top = p['thickness']+axial
        base = Part.makeBox(length+2*wall,width+2*wall,top-bottom,App.Vector(xmin-wall,ymin-wall,bottom))
        cavity = Part.makeBox(length,width,top+axial+1,App.Vector(xmin,ymin,-axial))
        base = base.cut(cavity)
        plate = Part.makeBox(length+2*wall,width+2*wall,wall,App.Vector(xmin-wall,ymin-wall,top))
        # A 1 mm deep/wide centering lip with 0.25 mm lateral clearance.
        lip = Part.makeBox(length-.5,width-.5,1,App.Vector(xmin+.25,ymin+.25,top-1))
        lip = lip.cut(Part.makeBox(length-2.5,width-2.5,3,App.Vector(xmin+1.25,ymin+1.25,top-2)))
        lid = plate.fuse(lip)
        for x in (0,layout['center_distance']):
            cutter = Part.makeCylinder((p['shaft_diameter']+p['housing_bore_clearance'])/2,
                                        top+wall-bottom+2,App.Vector(x,0,bottom-1))
            base,lid = base.cut(cutter),lid.cut(cutter)
        if p['lid_open']:
            lid.translate(App.Vector(0,width+2*wall+15,0))
        outputs.update(Caixa=base.removeSplitter(),Tampa=lid.removeSplitter())
    return outputs


def organizer(p):
    l,w,h,wall,floor = (p[k] for k in ('length','width','height','wall','floor'))
    rows,cols,t = p['rows'],p['columns'],p['divider']
    cell_l = (l-2*wall-(cols-1)*t)/cols
    cell_w = (w-2*wall-(rows-1)*t)/rows
    voids = [Part.makeBox(cell_l,cell_w,h,App.Vector(wall+c*(cell_l+t),wall+r*(cell_w+t),floor))
             for r in range(rows) for c in range(cols)]
    return {'Organizador': Part.makeBox(l,w,h).cut(Part.makeCompound(voids)).removeSplitter()}


def inset(face, distance):
    """Offset with a controlled 0.03 mm contour approximation for robust solids."""
    if distance == 0:
        return face.copy()
    # OCCT spline offsets can pass BOP checks yet lose shells on STEP export.
    # Offset a contour with <=0.03 mm chord deviation. The body's exterior
    # retains the exact font curves; cavity and inset-front contours use this bound.
    wires = []
    for wire in face.Wires:
        points = wire.discretize(Deflection=.03)
        if (points[-1] - points[0]).Length > 1e-7:
            points.append(points[0])
        wires.append(Part.Wire(Part.makePolygon(points).Edges))
    candidates = [Part.makeFace(wires, 'Part::FaceMakerBullseye')]
    for candidate in candidates:
        try:
            result = candidate.makeOffset2D(-distance, join=0, fill=False)
            # Intersect with the exact outline; never leave a cavity outside the glyph.
            result = result.common(face)
            if result.Faces and result.isValid() and result.Area > .01 and result.Area < face.Area:
                faces = []
                for surface in result.Faces:
                    surface = surface.copy()
                    if surface.normalAt(0,0).z < 0:
                        surface.reverse()
                    faces.append(surface)
                planar = faces[0] if len(faces) == 1 else Part.makeCompound(faces)
                # isValid alone misses faulty offset p-curves which break STEP/STL.
                planar.extrude(App.Vector(0,0,1)).check(True)
                return planar
        except (Part.OCCError, ValueError, RuntimeError):
            continue
    raise ValueError('Contorno fino ou complexo demais para essa parede/folga. Aumente a letra, reduza a parede ou troque a fonte.')


def channel(p):
    raw = Part.makeWireString(p['text'], p['font_file'], p['size'], p['spacing'])
    cap = Part.makeWireString('M', p['font_file'], p['size'], 0)
    if not cap or not cap[0]:
        raise ValueError('A fonte nao possui um contorno utilizavel.')
    cap_height = Part.makeCompound(cap[0]).BoundBox.YMax
    if cap_height <= 0:
        raise ValueError('Altura da fonte invalida.')
    scale = p['size']/cap_height
    faces = []
    for char in raw:
        if not char:
            continue
        for face in Part.makeFace(char, 'Part::FaceMakerBullseye').Faces:
            if face.normalAt(0,0).z < 0:
                face.reverse()
            face.scale(scale)
            faces.append(face)
    if not faces:
        raise ValueError('O texto nao gerou contornos. Troque a fonte.')
    bounds = Part.makeCompound(faces).BoundBox
    for face in faces:
        face.translate(App.Vector(-bounds.XMin,-bounds.YMin,0))
    bodies, fronts = [], []
    for face in faces:
        cavity_face = inset(face, p['wall'])
        cavity = cavity_face.extrude(App.Vector(0,0,p['depth']))
        cavity.translate(App.Vector(0,0,p['floor']))
        body = face.extrude(App.Vector(0,0,p['depth'])).cut(cavity).removeSplitter()
        checked(body, 'Corpo da letra/numero', detailed=True)
        bodies.append(body)
        if p['make_front']:
            front = inset(face,p['clearance']).extrude(App.Vector(0,0,p['front_thickness']))
            front.translate(App.Vector(0,-bounds.YLength-15,0))
            fronts.append(checked(front,'Frente', detailed=True))
    result = {'Corpos': Part.makeCompound(bodies)}
    if fronts:
        result['Frentes'] = Part.makeCompound(fronts)
    return result


@lru_cache(maxsize=8)
def _build_cached(kind, encoded, font_stamp):
    p = json.loads(encoded)
    from cess_gui.fasteners import build_fasteners
    outputs = {'gear':gear,'gear_pair':gear_pair,'fastener':build_fasteners,'box':box,'letters':channel,'numbers':channel,'organizer':organizer}[kind](p)
    return {name:checked(shape,name) for name,shape in outputs.items()}


def build_shapes(kind, params):
    p = validate(kind, params)
    stamp = None
    if 'font_file' in p:
        stat = Path(p['font_file']).stat()
        stamp = (stat.st_mtime_ns,stat.st_size)
    outputs = _build_cached(kind,json.dumps(p,sort_keys=True),stamp)
    return {name:shape.copy() for name,shape in outputs.items()}


def read_parameters(obj):
    result = {}
    for field in SPECS[obj.GeneratorKind][1]:
        value = getattr(obj,field.prop)
        result[field.key] = str(value) if field.type=='enum' else (value.Value if hasattr(value,'Value') else value)
    return result


class ParametersProxy:
    def execute(self, obj):
        try:
            values = validate(obj.GeneratorKind, read_parameters(obj))
            if obj.GeneratorKind == 'gear_pair':
                from cess_gui.gear_sets import gear_pair_layout
                info = gear_pair_layout(values)
                for prop,key in [('InputTeeth','input_teeth'),('OutputTeeth','output_teeth'),
                                 ('CenterDistance','center_distance'),('ContactRatio','contact_ratio'),
                                 ('SpeedMultiplier','speed_multiplier'),('TransmissionMode','mode')]:
                    setattr(obj,prop,info[key])
            obj.LastError = ''
        except Exception as error:
            obj.LastError = str(error)

    def dumps(self):
        return None

    def loads(self, state):
        pass


class GeneratedShapeProxy:
    def execute(self, obj):
        try:
            result = build_shapes(obj.Parameters.GeneratorKind, read_parameters(obj.Parameters))
            if obj.Element not in result:
                # A previously generated optional front was disabled.
                obj.Shape = Part.Shape()
            else:
                placement = App.Placement(obj.Placement)
                obj.Shape = Part.makeCompound([result[obj.Element]])
                obj.Placement = placement
            obj.LastError = ''
        except Exception as error:
            obj.Shape = Part.Shape()
            obj.LastError = str(error)
            App.Console.PrintError('CESS: ' + str(error) + '\n')

    def dumps(self):
        return None

    def loads(self, state):
        pass


def create_generator(kind, params=None, document=None, name='GeradorCESS'):
    values = validate(kind, params or {})
    shapes = build_shapes(kind,values)  # Validate before mutating a document.
    doc = document or App.ActiveDocument or App.newDocument('GeradoresCESS')
    doc.openTransaction('CESS: ' + SPECS[kind][0])
    try:
        group = doc.addObject('App::DocumentObjectGroup',name)
        group.Label = SPECS[kind][0]
        config = doc.addObject('App::FeaturePython',group.Name+'_Parametros')
        config.Label = 'Parametros - ' + SPECS[kind][0]
        config.addProperty('App::PropertyString','GeneratorKind','CESS')
        config.GeneratorKind = kind
        config.setEditorMode('GeneratorKind',1)
        config.addProperty('App::PropertyString','LastError','CESS')
        config.setEditorMode('LastError',1)
        types = {'length':'App::PropertyLength','float':'App::PropertyFloat',
                 'angle':'App::PropertyAngle','int':'App::PropertyInteger','bool':'App::PropertyBool',
                 'text':'App::PropertyString','font':'App::PropertyFile','enum':'App::PropertyEnumeration'}
        for field in SPECS[kind][1]:
            config.addProperty(types[field.type],field.prop,'Parametros',field.label)
            if field.type=='enum':
                setattr(config,field.prop,list(field.choices))
            setattr(config,field.prop,values[field.key])
        if kind == 'gear_pair':
            for prop,type_id in [('InputTeeth','Integer'),('OutputTeeth','Integer'),
                                 ('CenterDistance','Length'),('ContactRatio','Float'),
                                 ('SpeedMultiplier','Float'),('TransmissionMode','String')]:
                config.addProperty('App::Property'+type_id,prop,'Resultados')
                config.setEditorMode(prop,1)
        config.Proxy = ParametersProxy()
        group.addObject(config)
        outputs = []
        # Always create the optional front feature, so it can be toggled on later.
        elements = list(shapes)
        if kind in ('letters','numbers') and 'Frentes' not in elements:
            elements.append('Frentes')
        for element in elements:
            obj = doc.addObject('Part::FeaturePython',group.Name+'_'+element)
            obj.Label = element + ' - ' + SPECS[kind][0]
            obj.addProperty('App::PropertyLink','Parameters','CESS')
            obj.Parameters = config
            obj.addProperty('App::PropertyString','Element','CESS')
            obj.Element = element
            obj.addProperty('App::PropertyString','LastError','CESS')
            for prop in ('Parameters','Element','LastError'):
                obj.setEditorMode(prop,1)
            obj.Proxy = GeneratedShapeProxy()
            if App.GuiUp:
                obj.ViewObject.Proxy = 0
                colors = {'EngrenagemEntrada':(.2,.55,.9),'EngrenagemSaida':(.95,.65,.2),
                          'EixoEntrada':(.65,.65,.68),'EixoSaida':(.65,.65,.68),
                          'Caixa':(.35,.65,.45),'Tampa':(.35,.65,.45)}
                if kind == 'gear_pair':
                    obj.ViewObject.ShapeColor = colors.get(element,(.22,.57,.87))
                else:
                    obj.ViewObject.ShapeColor = (.95,.65,.2) if element in ('Tampa','Frentes') else (.22,.57,.87)
            group.addObject(obj)
            outputs.append(obj)
        doc.recompute()
        for obj in outputs:
            if obj.LastError:
                raise ValueError(obj.LastError)
            if obj.Element in shapes:
                checked(obj.Shape,obj.Label)
        doc.commitTransaction()
    except Exception:
        doc.abortTransaction()
        raise
    return {'group':group,'parameters':config,'objects':outputs}
