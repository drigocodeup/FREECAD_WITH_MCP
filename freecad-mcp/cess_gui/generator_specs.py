"""Shared GUI/CAD parameter contracts, independent of FreeCAD imports."""
from dataclasses import dataclass
import math
from pathlib import Path
import os


@dataclass(frozen=True)
class Field:
    key: str
    prop: str
    label: str
    type: str
    default: object
    minimum: float = 0
    maximum: float = 1000
    choices: tuple = ()


COMMON_BOX = (
    Field('length', 'Length', 'Comprimento externo', 'length', 120, 10, 2000),
    Field('width', 'Width', 'Largura externa', 'length', 80, 10, 2000),
    Field('height', 'Height', 'Altura da base', 'length', 40, 5, 1000),
    Field('wall', 'Wall', 'Espessura das paredes', 'length', 2, .4, 50),
    Field('floor', 'Floor', 'Espessura do fundo', 'length', 2, .4, 50),
)
CHANNEL = (
    Field('text', 'Text', 'Conteudo', 'text', 'CESS'),
    Field('font_file', 'FontFile', 'Fonte TTF/OTF', 'font', ''),
    Field('size', 'Size', 'Altura da letra maiuscula', 'length', 60, 10, 500),
    Field('depth', 'Depth', 'Profundidade total', 'length', 20, 2, 200),
    Field('wall', 'Wall', 'Espessura das paredes', 'length', 1.5, .4, 15),
    Field('floor', 'Floor', 'Espessura do fundo', 'length', 2, .4, 30),
    Field('spacing', 'Spacing', 'Espaco adicional entre caracteres', 'length', 5, 0, 100),
    Field('make_front', 'MakeFront', 'Gerar frente separada', 'bool', True),
    Field('front_thickness', 'FrontThickness', 'Espessura da frente', 'length', 1.5, .4, 30),
    Field('clearance', 'Clearance', 'Folga da frente por lado', 'length', .2, 0, 2),
)
SPECS = {
    'fastener': ('Parafuso e porca', (
        Field('head_type','HeadType','Tipo de cabeca','enum','allen',choices=('allen','sextavada')),
        Field('diameter','Diameter','Diametro nominal da rosca','length',8,2,40),
        Field('pitch','Pitch','Passo da rosca','length',1.25,.25,6),
        Field('length','Length','Comprimento sob a cabeca','length',30,3,200),
        Field('head_size','HeadSize','Diametro Allen / chave da cabeca sextavada','length',13,3,80),
        Field('head_height','HeadHeight','Altura da cabeca','length',8,1,40),
        Field('socket_size','SocketSize','Chave Allen (entre faces)','length',6,1,40),
        Field('socket_depth','SocketDepth','Profundidade do encaixe Allen','length',4,.5,30),
        Field('nut_size','NutSize','Chave da porca (entre faces)','length',13,3,80),
        Field('nut_height','NutHeight','Altura da porca','length',6.5,1,40),
        Field('clearance','Clearance','Folga diametral porca/parafuso','length',.3,.05,2),
        Field('left_hand','LeftHand','Rosca esquerda (desmarcada = direita)','bool',False),
    )),
    'gear_pair': ('Conjunto de engrenagens', (
        Field('ratio','Ratio','Voltas entrada:saida (ex.: 2:1)','text','2:1'),
        Field('minimum_teeth','MinimumTeeth','Minimo de dentes da menor engrenagem','int',20,12,100),
        Field('module','Module','Modulo','length',2,.3,20),
        Field('pressure_angle','PressureAngle','Angulo de pressao','angle',20,14.5,30),
        Field('thickness','Thickness','Espessura das engrenagens','length',10,1,200),
        Field('shaft_diameter','ShaftDiameter','Diametro dos dois eixos','length',8,1,100),
        Field('shaft_extension','ShaftExtension','Prolongamento do eixo em cada lado','length',10,3,100),
        Field('bore_clearance','BoreClearance','Folga diametral furo/eixo','length',.2,0,2),
        Field('center_clearance','CenterClearance','Acrescimo na distancia entre eixos','length',.1,0,2),
        Field('input_angle','InputAngle','Posicao angular da entrada','angle',0,0,36000),
        Field('make_housing','MakeHousing','Gerar caixa e tampa','bool',True),
        Field('housing_wall','HousingWall','Parede, fundo e tampa','length',3,2,20),
        Field('housing_clearance','HousingClearance','Folga radial interna da caixa','length',3,2,30),
        Field('axial_clearance','AxialClearance','Folga axial por lado','length',1.5,1.1,20),
        Field('housing_bore_clearance','HousingBoreClearance','Folga diametral eixo/caixa','length',.5,.1,3),
        Field('lid_open','LidOpen','Mostrar tampa separada','bool',True),
    )),
    'gear': ('Engrenagem', (
        Field('teeth', 'Teeth', 'Numero de dentes', 'int', 24, 12, 150),
        Field('module', 'Module', 'Modulo', 'length', 2, .3, 20),
        Field('pressure_angle', 'PressureAngle', 'Angulo de pressao', 'angle', 20, 14.5, 30),
        Field('thickness', 'Thickness', 'Espessura', 'length', 10, .5, 500),
        Field('bore', 'Bore', 'Diametro do furo (0 = sem furo)', 'length', 8, 0, 1000),
    )),
    'box': ('Caixa com tampa', COMMON_BOX + (
        Field('lid_thickness', 'LidThickness', 'Espessura da tampa', 'length', 2, .4, 50),
        Field('lip_depth', 'LipDepth', 'Profundidade da guia de encaixe', 'length', 5, 1, 100),
        Field('clearance', 'Clearance', 'Folga do encaixe por lado', 'length', .3, .05, 3),
    )),
    'letters': ('Letra caixa', CHANNEL),
    'numbers': ('Numeros caixa', tuple(
        Field(f.key, f.prop, f.label, f.type, '123' if f.key == 'text' else f.default, f.minimum, f.maximum)
        for f in CHANNEL)),
    'organizer': ('Organizador', COMMON_BOX + (
        Field('rows', 'Rows', 'Linhas', 'int', 2, 1, 20),
        Field('columns', 'Columns', 'Colunas', 'int', 3, 1, 20),
        Field('divider', 'Divider', 'Espessura das divisorias', 'length', 2, .4, 30),
    )),
}


def default_font():
    candidates = [Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts/arialbd.ttf',
                  Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')]
    return str(next((p for p in candidates if p.is_file()), ''))


def defaults(kind):
    if kind not in SPECS:
        raise ValueError('Gerador desconhecido.')
    result = {field.key: field.default for field in SPECS[kind][1]}
    if 'font_file' in result:
        result['font_file'] = default_font()
    return result


def validate(kind, params):
    values = defaults(kind)
    extra = set(params) - set(values)
    if extra:
        raise ValueError('Parametros desconhecidos: ' + ', '.join(sorted(extra)))
    values.update(params)
    for field in SPECS[kind][1]:
        value = values[field.key]
        if field.type == 'bool':
            if type(value) is not bool:
                raise ValueError(field.label + ': use verdadeiro ou falso.')
        elif field.type == 'enum':
            if not isinstance(value,str) or value not in field.choices:
                raise ValueError(field.label+': escolha '+', '.join(field.choices)+'.')
        elif field.type in ('text', 'font'):
            if not isinstance(value, str):
                raise ValueError(field.label + ': texto esperado.')
        else:
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(field.label + ': numero finito esperado.')
            if field.type == 'int' and type(value) is not int:
                raise ValueError(field.label + ': numero inteiro esperado.')
            if not field.minimum <= value <= field.maximum:
                raise ValueError(f'{field.label}: intervalo {field.minimum} a {field.maximum}.')
            if field.type != 'int':
                values[field.key] = float(value)
    if kind == 'fastener':
        d,p = values['diameter'],values['pitch']
        if p>d/3:
            raise ValueError('Passo excessivo para esse diametro; use passo ate diametro/3.')
        if values['length']<2*p or values['nut_height']<2*p:
            raise ValueError('Comprimento e altura da porca precisam comportar ao menos duas voltas.')
        if max(values['length'],values['nut_height'])/p>40:
            raise ValueError('Limite de 40 voltas de rosca real por peca. Aumente o passo ou reduza o comprimento.')
        if values['head_size']<=d+1:
            raise ValueError('Cabeca pequena demais para o diametro do parafuso.')
        if values['nut_size']<=d+values['clearance']+2:
            raise ValueError('Porca precisa de pelo menos 1 mm de parede radial alem da rosca.')
        if values['head_type']=='allen':
            if values['socket_depth']>=values['head_height']-.5:
                raise ValueError('O encaixe Allen precisa deixar ao menos 0,5 mm de fundo.')
            if values['socket_size']/math.sqrt(3)>=values['head_size']/2-.5:
                raise ValueError('Chave Allen grande demais para essa cabeca.')
    elif kind == 'gear_pair':
        from cess_gui.gear_sets import gear_pair_layout
        gear_pair_layout(values)
    elif kind == 'gear':
        root_diameter = values['module'] * (values['teeth'] - 2.5)
        if values['bore'] >= root_diameter - 2 * values['module']:
            raise ValueError('Furo grande demais: preserve material entre o furo e a raiz dos dentes.')
    elif kind in ('box', 'organizer'):
        inner_l = values['length'] - 2 * values['wall']
        inner_w = values['width'] - 2 * values['wall']
        if min(inner_l, inner_w) < 3 or values['height'] - values['floor'] < 2:
            raise ValueError('Paredes ou fundo eliminam o espaco interno da caixa.')
        if kind == 'box':
            if min(inner_l, inner_w) - 2*values['clearance'] - 2*values['wall'] < 2:
                raise ValueError('Guia da tampa nao cabe: reduza parede ou folga.')
            if values['lip_depth'] >= values['height'] - values['floor']:
                raise ValueError('Guia da tampa deve ser menor que a profundidade interna.')
        else:
            rows, cols = values['rows'], values['columns']
            if rows * cols > 100:
                raise ValueError('Limite de 100 compartimentos por organizador.')
            if min((inner_l-(cols-1)*values['divider'])/cols,
                   (inner_w-(rows-1)*values['divider'])/rows) < 3:
                raise ValueError('Compartimento menor que 3 mm: reduza linhas, colunas ou divisoria.')
    else:
        text = values['text']
        if not text.strip() or len(text) > 24 or '\n' in text or '\r' in text:
            raise ValueError('Use uma linha com 1 a 24 caracteres, incluindo espacos.')
        if kind == 'numbers' and not all(c in '0123456789 ' for c in text):
            raise ValueError('Numeros caixa aceita somente digitos de 0 a 9 e espacos.')
        if kind == 'letters' and not all(c.isalpha() or c == ' ' for c in text):
            raise ValueError('Letra caixa aceita letras e espacos; use Numeros caixa para digitos.')
        if values['floor'] >= values['depth']:
            raise ValueError('O fundo deve ser menor que a profundidade total.')
        if values['make_front'] and values['clearance'] >= values['wall']:
            raise ValueError('A folga da frente deve ser menor que a parede, para manter apoio para colagem.')
        font = Path(values['font_file'])
        if not font.is_file() or font.suffix.lower() not in ('.ttf', '.otf'):
            raise ValueError('Selecione um arquivo de fonte TTF ou OTF existente.')
    return values
