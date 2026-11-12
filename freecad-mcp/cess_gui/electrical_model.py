"""Validated drawing document, paper coordinates in millimetres (top-left origin)."""
from copy import deepcopy
from datetime import date
import json
import math
import re
from cess_gui.electrical_symbols import CATALOG

PAPERS={'A0':(841,1189),'A1':(594,841),'A2':(420,594),'A3':(297,420),'A4':(210,297)}
META={'company':'','title':'Projeto eletrico','project':'','author':'','checked':'','revision':'0',
      'date':'','sheet':'1','sheets':'1'}


def text(value,name,limit=80):
    if not isinstance(value,str) or len(value)>limit or any(ord(c)<32 and c!='\n' for c in value):
        raise ValueError(f'{name}: texto de ate {limit} caracteres esperado.')
    return value


def number(value,name):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
        raise ValueError(name+': numero finito esperado.')
    return float(value)


def identifier(value):
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,39}',value):
        raise ValueError('ID invalido: letra inicial e ate 40 letras ASCII, digitos ou _.')
    return value


def dimensions(model):
    w,h=PAPERS[model['paper']]
    return (h,w) if model['orientation']=='landscape' else (w,h)


def drawing_bounds(model):
    w,h=dimensions(model)
    return (20,10,w-10,h-50)


def new_drawing(paper='A3',orientation='landscape',metadata=None):
    m=dict(version=1,paper=paper,orientation=orientation,grid=5,
           metadata={**META,'date':date.today().isoformat(),**(metadata or {})},symbols=[],wires=[],notes=[])
    return validate(m)


def transform(component,point):
    a=math.radians(component['rotation']);x,y=point
    return [component['x']+x*math.cos(a)-y*math.sin(a),component['y']+x*math.sin(a)+y*math.cos(a)]


def pin_position(component,pin):
    for name,x,y in CATALOG[component['kind']]['pins']:
        if name==pin:return transform(component,(x,y))
    raise ValueError('Terminal inexistente: '+str(pin))


def endpoint(model,ref):
    if not isinstance(ref,dict):raise ValueError('Extremidade de fio invalida.')
    if set(ref)=={'point'}:
        return point(ref['point'])
    if set(ref)=={'symbol','pin'}:
        item=next((s for s in model['symbols'] if s['id']==ref['symbol']),None)
        if item is None:raise ValueError('Fio referencia simbolo inexistente.')
        return pin_position(item,ref['pin'])
    raise ValueError('Fio: use {symbol,pin} ou {point:[x,y]}.')


def point(p):
    if not isinstance(p,(list,tuple)) or len(p)!=2:raise ValueError('Ponto deve ser [x,y].')
    return [number(p[0],'X'),number(p[1],'Y')]


def inside(model,p,padding=0):
    x0,y0,x1,y1=drawing_bounds(model);x,y=p
    if not x0+padding<=x<=x1-padding or not y0+padding<=y<=y1-padding:
        raise ValueError('Desenho ultrapassa as margens ou o quadro inferior da prancha.')


def wire_points(model,wire):
    targets=[endpoint(model,wire['start']),*wire.get('waypoints',[]),endpoint(model,wire['end'])]
    result=[targets[0]]
    for target in targets[1:]:
        prev=result[-1]
        if abs(prev[0]-target[0])>1e-8 and abs(prev[1]-target[1])>1e-8:
            result.append([prev[0],target[1]])
        if target!=result[-1]:result.append(list(target))
    return result


def validate(raw):
    if not isinstance(raw,dict) or set(raw)!={'version','paper','orientation','grid','metadata','symbols','wires','notes'}:
        raise ValueError('Estrutura do desenho invalida.')
    m=deepcopy(raw)
    if type(m['version']) is not int or m['version']!=1 or not isinstance(m['paper'],str) or m['paper'] not in PAPERS or m['orientation'] not in ('landscape','portrait'):
        raise ValueError('Use formato A0 a A4 e orientacao landscape ou portrait.')
    m['grid']=number(m['grid'],'Grade')
    if not .5<=m['grid']<=20:raise ValueError('Grade deve estar entre 0,5 e 20 mm.')
    if not isinstance(m['metadata'],dict) or set(m['metadata'])!=set(META):raise ValueError('Carimbo invalido.')
    for k,v in m['metadata'].items():text(v,k,80 if k=='title' else 50)
    for key in ('sheet','sheets'):
        if not re.fullmatch(r'[0-9]{1,3}',m['metadata'][key]) or int(m['metadata'][key])<1:
            raise ValueError('Folha e total de folhas: inteiros de 1 a 999.')
    if int(m['metadata']['sheet'])>int(m['metadata']['sheets']):raise ValueError('Numero da folha excede o total.')
    text(m['metadata']['revision'],'Revisao',12);text(m['metadata']['date'],'Data',20)
    for key,limit in [('symbols',500),('wires',1000),('notes',200)]:
        if not isinstance(m[key],list) or len(m[key])>limit:raise ValueError(f'Limite de {limit} itens em {key}.')
    ids=set()
    for s in m['symbols']:
        if not isinstance(s,dict) or set(s)!={'id','kind','tag','description','x','y','rotation'}:raise ValueError('Simbolo invalido.')
        identifier(s['id'])
        if s['id'] in ids or s['kind'] not in CATALOG:raise ValueError('ID duplicado ou simbolo desconhecido.')
        ids.add(s['id']);text(s['tag'],'Identificacao',24);text(s['description'],'Descricao',80)
        for k in ('x','y','rotation'):s[k]=number(s[k],k)
        if s['rotation']%90:raise ValueError('Rotacao deve ser multipla de 90 graus.')
        s['rotation']%=360
        # Include geometry and its horizontal identification/description labels.
        for p in [transform(s,(-9,-11)),transform(s,(9,11))]:inside(m,p)
        label_width=max(len(s['tag'])*1.55,min(len(s['description']),22)*1.1)
        label_bottom=max(10,4+3*(max(1,math.ceil(len(s['description'])/22))-1))
        inside(m,[s['x']+7+label_width,s['y']+label_bottom])
    for wire in m['wires']:
        if not isinstance(wire,dict) or set(wire)!={'id','start','end','waypoints','label','color'}:raise ValueError('Fio invalido.')
        identifier(wire['id'])
        if wire['id'] in ids:raise ValueError('ID duplicado.')
        ids.add(wire['id']);text(wire['label'],'Numero do fio',20)
        if not isinstance(wire['color'],str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',wire['color']):raise ValueError('Cor deve ser #RRGGBB.')
        if not isinstance(wire['waypoints'],list) or len(wire['waypoints'])>40:raise ValueError('Maximo de 40 pontos intermediarios.')
        wire['waypoints']=[point(p) for p in wire['waypoints']]
        pts=wire_points(m,wire)
        if len(pts)<2:raise ValueError('Conexao com comprimento zero.')
        for p in pts:inside(m,p)
    for note in m['notes']:
        if not isinstance(note,dict) or set(note)!={'id','text','x','y','size'}:raise ValueError('Anotacao invalida.')
        identifier(note['id'])
        if note['id'] in ids:raise ValueError('ID duplicado.')
        ids.add(note['id']);text(note['text'],'Anotacao',500)
        note['size']=number(note['size'],'Altura do texto')
        if not 1.5<=note['size']<=10:raise ValueError('Texto: altura de 1,5 a 10 mm.')
        for k in ('x','y'):note[k]=number(note[k],k)
        inside(m,[note['x'],note['y']]);inside(m,[note['x']+max((len(l) for l in note['text'].splitlines()),default=0)*note['size']*.65,
                                                    note['y']+max(1,len(note['text'].splitlines()))*note['size']*1.4])
    if len(json.dumps(m,ensure_ascii=False).encode('utf-8'))>512000:raise ValueError('Desenho excede 512 KiB.')
    return m


def next_id(model,prefix):
    used={i['id'] for k in ('symbols','wires','notes') for i in model[k]}
    n=1
    while prefix+str(n) in used:n+=1
    return prefix+str(n)


def add_symbol(model,kind,x,y,tag='',rotation=0,description=''):
    m=deepcopy(model)
    if kind not in CATALOG:raise ValueError('Simbolo desconhecido.')
    if not tag and CATALOG[kind]['prefix']:
        used={s['tag'] for s in m['symbols']};n=1;prefix=CATALOG[kind]['prefix']
        while prefix+str(n) in used:n+=1
        tag=prefix+str(n)
    s=dict(id=next_id(m,'C'),kind=kind,tag=tag,description=description,x=x,y=y,rotation=rotation)
    m['symbols'].append(s)
    return validate(m),s['id']


def add_wire(model,start,end,label='',waypoints=None,color='#111111'):
    m=deepcopy(model);wid=next_id(m,'W')
    m['wires'].append(dict(id=wid,start=start,end=end,waypoints=waypoints or [],label=label,color=color))
    return validate(m),wid


def remove_item(model,item_id):
    m=deepcopy(model)
    m['symbols']=[s for s in m['symbols'] if s['id']!=item_id]
    m['notes']=[n for n in m['notes'] if n['id']!=item_id]
    m['wires']=[w for w in m['wires'] if w['id']!=item_id and all(w[e].get('symbol')!=item_id for e in ('start','end'))]
    return validate(m)
