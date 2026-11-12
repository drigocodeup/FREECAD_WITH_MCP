"""Deterministic, escaped vector rendering for editor, TechDraw and printing."""
from html import escape
import textwrap
from cess_gui.electrical_model import validate,dimensions,wire_points,pin_position
from cess_gui.electrical_symbols import CATALOG


def label(x,y,value,size=2.5,anchor='start',color='#111111'):
    return f'<text x="{x:g}" y="{y:g}" font-family="Arial,DejaVu Sans,sans-serif" font-size="{size:g}" text-anchor="{anchor}" fill="{color}">{escape(str(value))}</text>'


def lines_of_text(x,y,value,width=36,size=2.4):
    rows=textwrap.wrap(value.replace('\n',' '),width=width) or ['']
    return ''.join(label(x,y+i*size*1.25,line,size) for i,line in enumerate(rows))


def symbol_fragment(s):
    spec=CATALOG[s['kind']];shapes=[]
    for primitive in spec['geometry']:
        kind,*v=primitive
        if kind in ('L','D'):
            x1,y1,x2,y2=v
            dash=' stroke-dasharray="1 .7"' if kind=='D' else ''
            shapes.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"{dash}/>')
        elif kind=='R':
            x,y,w,h=v;shapes.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}"/>')
        elif kind in ('C','F'):
            x,y,r=v;shapes.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="'+('#111111' if kind=='F' else 'white')+'"/>')
        elif kind=='T':
            x,y,value,size=v;shapes.append(label(x,y,value,size))
    geometry=f'<g transform="translate({s["x"]:g} {s["y"]:g}) rotate({s["rotation"]:g})" stroke="#111111" stroke-width=".35" fill="none">'+''.join(shapes)+'</g>'
    texts=label(s['x']+7,s['y']-2,s['tag'],3)
    texts+=lines_of_text(s['x']+7,s['y']+2,s['description'],22,2.2)
    if s['kind']!='junction':
        for name,_,_ in spec['pins']:
            x,y=pin_position(s,name)
            texts+=label(x+1.3,y-.8,name,1.7)
    return '<g data-symbol="'+escape(s['id'],quote=True)+'">'+geometry+texts+'</g>'


def standalone_symbol(component):
    s=dict(component,x=0,y=0)
    return '<svg xmlns="http://www.w3.org/2000/svg" width="70" height="40" viewBox="-12 -14 70 40">'+symbol_fragment(s)+'</svg>'


def frame(model):
    w,h=dimensions(model);x,y=w-190,h-45;meta=model['metadata']
    parts=[f'<rect x="20" y="10" width="{w-30}" height="{h-20}" fill="none" stroke="#111111" stroke-width=".5"/>',
           f'<rect x="{x}" y="{y}" width="180" height="35" fill="white" stroke="#111111" stroke-width=".35"/>']
    def line(x1,y1,x2,y2):return f'<path d="M{x1:g},{y1:g} L{x2:g},{y2:g}" stroke="#111111" stroke-width=".25"/>'
    parts.extend([line(x,y+14,x+180,y+14),line(x,y+24,x+180,y+24),line(x+80,y,x+80,y+14)])
    parts.extend([label(x+2,y+3,'EMPRESA / ESCOLA',1.8),lines_of_text(x+2,y+7,meta['company'],40,2.5),
                  label(x+82,y+3,'TITULO DO PROJETO',1.8),lines_of_text(x+82,y+7,meta['title'],52,2.5)])
    for i,(key,title) in enumerate([('project','PROJETO / CODIGO'),('author','RESPONSAVEL'),('checked','VERIFICADO')]):
        xx=x+i*60
        if i:parts.append(line(xx,y+14,xx,y+24))
        parts.extend([label(xx+2,y+17,title,1.8),lines_of_text(xx+2,y+20,meta[key],37,2.2)])
    cells=[(25,'REVISAO',meta['revision']),(40,'DATA',meta['date']),
           (25,'FOLHA',meta['sheet']+'/'+meta['sheets']),(25,'FORMATO',model['paper']),
           (65,'ESCALA / DISCIPLINA','SEM ESCALA / ELETRICA')]
    xx=x
    for i,(width,title,value) in enumerate(cells):
        if i:parts.append(line(xx,y+24,xx,y+35))
        parts.extend([label(xx+2,y+27,title,1.8),label(xx+2,y+32,value,2.5)])
        xx+=width
    return ''.join(parts)


def render_svg(raw,contents=True):
    model=validate(raw);w,h=dimensions(model)
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}">',
           '<title>'+escape(model['metadata']['title'])+'</title>',f'<rect width="{w}" height="{h}" fill="white"/>',frame(model)]
    if contents:
        for wire in model['wires']:
            pts=wire_points(model,wire);coords=' '.join(f'{x:g},{y:g}' for x,y in pts)
            parts.append(f'<polyline data-wire="{escape(wire["id"],quote=True)}" points="{coords}" fill="none" stroke="{wire["color"]}" stroke-width=".35" stroke-linejoin="round"/>')
            if wire['label']:
                a,b=pts[0],pts[1];parts.append(label((a[0]+b[0])/2+1,(a[1]+b[1])/2-1,wire['label'],2))
        parts.extend(symbol_fragment(s) for s in model['symbols'])
        for note in model['notes']:
            for i,row in enumerate(note['text'].splitlines()):
                parts.append(label(note['x'],note['y']+note['size']+i*note['size']*1.4,row,note['size']))
    parts.append('</svg>')
    return ''.join(parts)
