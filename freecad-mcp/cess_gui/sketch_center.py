"""Center rectangular loops inside one sketch using its own constraint solver."""
import math

def rectangle_groups(segments,tolerance=1e-5):
    nodes=[];edges=[]
    def node(point):
        for i,p in enumerate(nodes):
            if math.dist(point,p)<=tolerance:return i
        nodes.append(tuple(point));return len(nodes)-1
    for index,start,end in segments:edges.append((index,node(start),node(end)))
    adjacent={v:[] for v in range(len(nodes))}
    for e,(_,a,b) in enumerate(edges):
        if a!=b:adjacent[a].append((e,b));adjacent[b].append((e,a))
    cycles=set();result=[]
    def walk(start,current,path,visited):
        for edge,other in adjacent[current]:
            if edge in path:continue
            if len(path)==3:
                if other==start:cycles.add(tuple(sorted((*path,edge))))
            elif other not in visited:walk(start,other,(*path,edge),visited|{other})
        if len(cycles)>128:raise ValueError('Contornos sobrepostos ambiguos: selecione um esboco mais simples.')
    for vertex in adjacent:walk(vertex,vertex,(),{vertex})
    for component in cycles:
        vertices={v for e in component for v in edges[e][1:]}
        if len(vertices)!=4:continue
        points=[nodes[v] for v in vertices];xs=[p[0] for p in points];ys=[p[1] for p in points]
        bounds=(min(xs),min(ys),max(xs),max(ys));x0,y0,x1,y1=bounds
        if min(x1-x0,y1-y0)<=tolerance:continue
        if any(not (abs(nodes[a][0]-nodes[b][0])<=tolerance or abs(nodes[a][1]-nodes[b][1])<=tolerance)
               for _,a,b in (edges[e] for e in component)):continue
        result.append(dict(edges=sorted(edges[e][0] for e in component),bounds=bounds,
                           center=((x0+x1)/2,(y0+y1)/2),size=(x1-x0,y1-y0)))
    return sorted(result,key=lambda r:r['size'][0]*r['size'][1])

def sketch_rectangles(sketch):
    segments=[]
    for i,g in enumerate(sketch.Geometry):
        if g.TypeId=='Part::GeomLineSegment' and not sketch.getConstruction(i):
            segments.append((i,(g.StartPoint.x,g.StartPoint.y),(g.EndPoint.x,g.EndPoint.y)))
    return rectangle_groups(segments)

def center_sketch_rectangles(sketch,moving_edges,reference_edges,axes='XY'):
    import FreeCAD as App
    if axes not in ('X','Y','XY'):raise ValueError('No esboco, escolha X, Y ou XY.')
    if set(moving_edges).intersection(reference_edges):raise ValueError('Escolha dois retangulos diferentes.')
    def find(edges):
        group=next((g for g in sketch_rectangles(sketch) if g['edges']==sorted(edges)),None)
        if group is None:raise ValueError('Selecione dois contornos retangulares fechados e paralelos aos eixos do esboco.')
        return group
    moving,reference=find(moving_edges),find(reference_edges)
    delta=[reference['center'][i]-moving['center'][i] if axis in axes else 0 for i,axis in enumerate('XY')]
    if max(abs(v) for v in delta)<1e-7:return dict(translation_mm=delta,axes=axes)
    doc=sketch.Document;doc.openTransaction('CESS: centralizar retangulos no Sketcher')
    try:
        # Drag each endpoint through the solver. Existing dimensions and constraints remain intact.
        sketch.moveGeometries([(i,p) for i in moving['edges'] for p in (1,2)],App.Vector(*delta,0),True)
        if sketch.solve()!=0:raise ValueError('O solver nao aceitou a centralizacao com as restricoes atuais.')
        doc.recompute();actual,ref_after=find(moving_edges),find(reference_edges)
        unchanged=all(abs(a-b)<1e-6 for a,b in zip(reference['bounds'],ref_after['bounds']))
        sized=all(abs(a-b)<1e-6 for a,b in zip(moving['size'],actual['size']))
        centered=all(abs(actual['center'][i]-reference['center'][i])<1e-6 for i,axis in enumerate('XY') if axis in axes)
        untouched_axes=all(abs(actual['center'][i]-moving['center'][i])<1e-6 for i,axis in enumerate('XY') if axis not in axes)
        if not (unchanged and sized and centered and untouched_axes):
            raise ValueError('As restricoes impedem mover somente este retangulo. Revise cotas de posicao, fixacoes ou vinculos entre contornos; nenhuma restricao foi removida.')
        doc.commitTransaction()
    except Exception:
        doc.abortTransaction();doc.recompute();raise
    return dict(translation_mm=delta,axes=axes,center=list(actual['center']))
