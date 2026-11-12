"""Allowlisted CAD operations. Called exclusively by the Qt main thread."""
import inspect
import re
import sys
from pathlib import Path
import FreeCAD as App
import FreeCADGui as Gui
import Part
from bridge.geometry import number, vector, safe_path, shape_info


class Operations:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.allowed = {name: getattr(self, name) for name in (
            'health_check', 'new_document', 'open_document', 'list_documents',
            'save_document', 'close_document', 'create_box', 'create_cylinder',
            'create_sphere', 'create_cone', 'create_torus', 'boolean_union',
            'boolean_cut', 'boolean_intersection', 'move_object', 'rotate_object',
            'copy_object', 'delete_object', 'list_objects', 'get_object_properties',
            'get_bounding_box', 'get_volume', 'validate_shape', 'export_step',
            'export_stl', 'save_fcstd', 'fit_all', 'set_view', 'capture_view',
            'generate_gear', 'generate_gear_pair', 'generate_fastener', 'generate_box_with_lid', 'generate_channel_letters',
            'generate_channel_numbers', 'generate_organizer')}

    def dispatch(self, operation, params):
        if operation not in self.allowed:
            raise ValueError('Operacao nao permitida')
        fn = self.allowed[operation]
        inspect.signature(fn).bind(**params)
        return fn(**params)

    def doc(self, document):
        d = App.listDocuments().get(document)
        if d is None:
            raise ValueError(f'Documento inexistente: {document}')
        return d

    def obj(self, document, object_name):
        o = self.doc(document).getObject(object_name)
        if o is None:
            raise ValueError(f'Objeto inexistente: {object_name}; use o Name retornado')
        return o

    def name(self, name):
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,79}', name):
            raise ValueError('Nome: letra inicial, letras ASCII, numeros ou _, ate 80 caracteres')
        return name

    def unused(self, document, name):
        self.name(name)
        if self.doc(document).getObject(name):
            raise ValueError(f'Nome de objeto ja existe: {name}')

    def info(self, o):
        self.doc(o.Document.Name).recompute()
        return {'document': o.Document.Name, 'name': o.Name, 'label': o.Label,
                'type': o.TypeId, **shape_info(o.Shape)}

    def health_check(self):
        return {'freecad_version': App.Version(), 'python': sys.version,
                'gui': bool(App.GuiUp), 'documents': list(App.listDocuments()),
                'workspace': str(self.root), 'thread': 'Qt GUI main thread',
                'units': 'mm', 'operations': sorted(self.allowed)}

    def generated(self, kind, document, name, params):
        from cess_gui.generators import create_generator
        self.unused(document,name)
        result = create_generator(kind,params,self.doc(document),name)
        return {'document':document, 'group':result['group'].Name,
                'parameter_object':result['parameters'].Name,
                'objects':[self.info(o) for o in result['objects'] if not o.Shape.isNull()]}

    def generate_gear(self, document, name, teeth=24, module=2, pressure_angle=20, thickness=10, bore=8):
        return self.generated('gear',document,name,dict(teeth=teeth,module=module,pressure_angle=pressure_angle,
                                                      thickness=thickness,bore=bore))

    def generate_gear_pair(self, document, name, ratio='2:1', minimum_teeth=20, module=2, pressure_angle=20,
                           thickness=10, shaft_diameter=8, shaft_extension=10, bore_clearance=.2,
                           center_clearance=.1, input_angle=0, make_housing=True, housing_wall=3,
                           housing_clearance=3, axial_clearance=1.5, housing_bore_clearance=.5, lid_open=True):
        params = dict(locals())
        for key in ('self','document','name'):
            params.pop(key)
        result = self.generated('gear_pair',document,name,params)
        from cess_gui.gear_sets import gear_pair_layout
        result['transmission'] = gear_pair_layout(params)
        return result

    def generate_fastener(self, document, name, head_type='allen', diameter=8, pitch=1.25, length=30,
                          head_size=13, head_height=8, socket_size=6, socket_depth=4, nut_size=13,
                          nut_height=6.5, clearance=.3, left_hand=False):
        params = dict(locals())
        for key in ('self','document','name'):
            params.pop(key)
        return self.generated('fastener',document,name,params)

    def generate_box_with_lid(self, document, name, length=120, width=80, height=40, wall=2, floor=2,
                              lid_thickness=2, lip_depth=5, clearance=.3):
        return self.generated('box',document,name,dict(length=length,width=width,height=height,wall=wall,floor=floor,
                              lid_thickness=lid_thickness,lip_depth=lip_depth,clearance=clearance))

    def generate_channel_letters(self, document, name, text='CESS', font_file='', size=60, depth=20,
                                 wall=1.5, floor=2, spacing=5, make_front=True, front_thickness=1.5, clearance=.2):
        from cess_gui.generator_specs import default_font
        return self.generated('letters',document,name,dict(text=text,font_file=font_file or default_font(),size=size,
                              depth=depth,wall=wall,floor=floor,spacing=spacing,make_front=make_front,
                              front_thickness=front_thickness,clearance=clearance))

    def generate_channel_numbers(self, document, name, text='123', font_file='', size=60, depth=20,
                                 wall=1.5, floor=2, spacing=5, make_front=True, front_thickness=1.5, clearance=.2):
        from cess_gui.generator_specs import default_font
        return self.generated('numbers',document,name,dict(text=text,font_file=font_file or default_font(),size=size,
                              depth=depth,wall=wall,floor=floor,spacing=spacing,make_front=make_front,
                              front_thickness=front_thickness,clearance=clearance))

    def generate_organizer(self, document, name, length=120, width=80, height=40, wall=2, floor=2,
                           rows=2, columns=3, divider=2):
        return self.generated('organizer',document,name,dict(length=length,width=width,height=height,wall=wall,
                              floor=floor,rows=rows,columns=columns,divider=divider))

    def new_document(self, name):
        self.name(name)
        if name in App.listDocuments():
            raise ValueError('Documento ja existe')
        d = App.newDocument(name)
        return {'document': d.Name}

    def list_documents(self):
        return {'documents': [{'name': d.Name, 'label': d.Label, 'file': d.FileName}
                              for d in App.listDocuments().values()]}

    def open_document(self, filename):
        p = safe_path(self.root, filename, '.FCStd')
        if not p.is_file():
            raise ValueError('Arquivo nao encontrado')
        if any(d.FileName and Path(d.FileName).resolve() == p for d in App.listDocuments().values()):
            raise ValueError('Arquivo ja esta aberto')
        d = App.openDocument(str(p))
        d.recompute()
        return {'document': d.Name, 'objects': len(d.Objects)}

    def save_document(self, document, filename, overwrite=False):
        p = safe_path(self.root, filename, '.FCStd')
        self.prepare_file(p, overwrite)
        d = self.doc(document)
        d.recompute()
        d.saveAs(str(p))
        Gui.getDocument(document).Modified = False
        return {'path': str(p), 'bytes': p.stat().st_size}

    save_fcstd = save_document

    def close_document(self, document, discard=False):
        if type(discard) is not bool:
            raise ValueError('discard deve ser booleano')
        d = self.doc(document)
        if Gui.getDocument(document).Modified and not discard:
            raise ValueError('Documento modificado: salve ou informe discard=true')
        App.closeDocument(document)
        return {'closed': document}

    def primitive(self, document, name, type_id, props, position):
        self.unused(document, name)
        xyz = vector(position)
        d = self.doc(document)
        d.openTransaction('MCP primitive')
        try:
            o = d.addObject(type_id, name)
            for key, val in props.items():
                if type_id == 'Part::Cone' and key in ('Radius1', 'Radius2'):
                    v = number(val, key)
                    if v < 0:
                        raise ValueError('Raio negativo')
                else:
                    v = number(val, key, positive=True)
                setattr(o, key, v)
            o.Placement.Base = App.Vector(*xyz)
            result = self.info(o)
            if not result['valid'] or result['solids'] != 1:
                raise ValueError('Primitiva nao produziu solido valido')
            d.commitTransaction()
            return result
        except Exception:
            d.abortTransaction()
            raise

    def create_box(self, document, name, length, width, height, position=(0, 0, 0)):
        return self.primitive(document, name, 'Part::Box',
                              {'Length': length, 'Width': width, 'Height': height}, position)

    def create_cylinder(self, document, name, radius, height, position=(0, 0, 0)):
        return self.primitive(document, name, 'Part::Cylinder', {'Radius': radius, 'Height': height}, position)

    def create_sphere(self, document, name, radius, position=(0, 0, 0)):
        return self.primitive(document, name, 'Part::Sphere', {'Radius': radius}, position)

    def create_cone(self, document, name, radius1, radius2, height, position=(0, 0, 0)):
        # FreeCAD permits a zero radius at one end.
        for r in (radius1, radius2):
            if number(r, 'raio') < 0:
                raise ValueError('Raio negativo')
        if radius1 == radius2 == 0:
            raise ValueError('Ao menos um raio deve ser positivo')
        return self.primitive(document, name, 'Part::Cone',
                              {'Radius1': radius1, 'Radius2': radius2, 'Height': height}, position)

    def create_torus(self, document, name, radius1, radius2, position=(0, 0, 0)):
        if number(radius1, 'radius1', True) <= number(radius2, 'radius2', True):
            raise ValueError('Raio maior deve exceder raio do tubo')
        return self.primitive(document, name, 'Part::Torus', {'Radius1': radius1, 'Radius2': radius2}, position)

    def feature(self, document, name, shape, position=(0, 0, 0)):
        self.unused(document, name)
        result = shape_info(shape)
        if not result['valid']:
            raise ValueError('Geometria invalida')
        xyz = vector(position)
        o = self.doc(document).addObject('Part::Feature', name)
        o.Shape = shape
        o.Placement.Base = App.Vector(*xyz)
        return self.info(o)

    def boolean(self, document, name, base, tool, type_id):
        self.unused(document, name)
        a, b = self.obj(document, base), self.obj(document, tool)
        if a == b:
            raise ValueError('Selecione objetos diferentes')
        d = self.doc(document)
        d.openTransaction('MCP boolean')
        try:
            o = d.addObject(type_id, name)
            o.Base, o.Tool = a, b
            result = self.info(o)
            if not result['valid'] or result['solids'] < 1:
                raise ValueError('Operacao nao produziu solido valido')
            a.Visibility = b.Visibility = False
            d.commitTransaction()
            return result
        except Exception:
            d.abortTransaction()
            raise

    def boolean_union(self, document, name, base, tool):
        return self.boolean(document, name, base, tool, 'Part::Fuse')

    def boolean_cut(self, document, name, base, tool):
        return self.boolean(document, name, base, tool, 'Part::Cut')

    def boolean_intersection(self, document, name, base, tool):
        return self.boolean(document, name, base, tool, 'Part::Common')

    def move_object(self, document, object_name, position):
        o = self.obj(document, object_name)
        o.Placement.Base = App.Vector(*vector(position))
        return self.info(o)

    def rotate_object(self, document, object_name, axis, angle):
        o = self.obj(document, object_name)
        axis = vector(axis)
        if sum(v*v for v in axis) == 0:
            raise ValueError('Eixo nulo')
        o.Placement.Rotation = App.Rotation(App.Vector(*axis), number(angle, 'angle'))
        return self.info(o)

    def copy_object(self, document, object_name, name):
        o = self.obj(document, object_name)
        # Linked copy preserves source reference and placement.
        self.unused(document, name)
        copy = self.doc(document).addObject('App::Link', name)
        copy.setLink(o)
        return self.info(copy)

    def delete_object(self, document, object_name):
        o = self.obj(document, object_name)
        if o.InList:
            raise ValueError('Objeto possui dependentes; remova-os primeiro')
        self.doc(document).removeObject(o.Name)
        self.doc(document).recompute()
        return {'deleted': object_name}

    def list_objects(self, document):
        return {'objects': [{'name': o.Name, 'label': o.Label, 'type': o.TypeId,
                             'dependencies': [x.Name for x in o.OutList]}
                            for o in self.doc(document).Objects]}

    def get_object_properties(self, document, object_name):
        o = self.obj(document, object_name)
        return {**self.info(o), 'position': list(o.Placement.Base),
                'dependencies': [x.Name for x in o.OutList],
                'properties': {p: str(getattr(o, p)) for p in o.PropertiesList
                               if p not in ('Shape', 'Mesh')}}

    def get_bounding_box(self, document, object_name):
        return {'bounding_box': self.info(self.obj(document, object_name))['bounding_box']}

    def get_volume(self, document, object_name):
        return {'volume_mm3': self.info(self.obj(document, object_name))['volume_mm3']}

    def validate_shape(self, document, object_name):
        return self.info(self.obj(document, object_name))

    def prepare_file(self, path, overwrite):
        if type(overwrite) is not bool:
            raise ValueError('overwrite deve ser booleano')
        if path.exists() and not overwrite:
            raise ValueError('Arquivo ja existe; escolha outro nome ou overwrite=true')
        path.parent.mkdir(parents=True, exist_ok=True)

    def export(self, document, object_names, filename, kind, overwrite):
        suffix = {'step': '.step', 'stl': '.stl'}[kind]
        p = safe_path(self.root, filename, suffix)
        if not isinstance(object_names, list) or not object_names:
            raise ValueError('Selecione ao menos um objeto')
        objects = [self.obj(document, n) for n in object_names]
        for o in objects:
            if not self.info(o)['valid']:
                raise ValueError('Objeto invalido')
        self.prepare_file(p, overwrite)
        if kind == 'step':
            Part.export(objects, str(p))
        else:
            import Mesh
            Mesh.export(objects, str(p))
        return {'path': str(p), 'bytes': p.stat().st_size}

    def export_step(self, document, object_names, filename, overwrite=False):
        return self.export(document, object_names, filename, 'step', overwrite)

    def export_stl(self, document, object_names, filename, overwrite=False):
        return self.export(document, object_names, filename, 'stl', overwrite)

    def fit_all(self, document):
        self.doc(document)
        Gui.getDocument(document).activeView().fitAll()
        return {'view': 'fit_all'}

    def set_view(self, document, view):
        views = {'isometric': 'viewAxonometric', 'front': 'viewFront', 'rear': 'viewRear',
                 'top': 'viewTop', 'bottom': 'viewBottom', 'left': 'viewLeft', 'right': 'viewRight'}
        if view not in views:
            raise ValueError('Vista permitida: ' + ', '.join(views))
        self.doc(document)
        getattr(Gui.getDocument(document).activeView(), views[view])()
        return {'view': view}

    def capture_view(self, document, filename, width=1200, height=800, overwrite=False):
        p = safe_path(self.root, filename, '.png')
        for n in (width, height):
            if type(n) is not int or not 64 <= n <= 4096:
                raise ValueError('Dimensoes da imagem: inteiros entre 64 e 4096')
        self.doc(document)
        self.prepare_file(p, overwrite)
        Gui.getDocument(document).activeView().saveImage(str(p), width, height, 'Current')
        return {'path': str(p), 'bytes': p.stat().st_size}
