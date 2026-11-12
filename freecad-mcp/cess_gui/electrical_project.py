"""FreeCAD electrical document controller and native TechDraw project sheet."""
import hashlib
import json
from pathlib import Path
import re
import FreeCAD as App
from cess_gui.electrical_model import validate,new_drawing,dimensions,drawing_bounds,META,PAPERS
from cess_gui.electrical_svg import render_svg

PROJECT=Path(__file__).resolve().parents[1]
META_PROPS={'company':'Company','title':'Title','project':'ProjectCode','author':'Author','checked':'CheckedBy',
            'revision':'Revision','date':'Date','sheet':'SheetNumber','sheets':'SheetCount'}


def is_sheet(obj):
    return hasattr(obj,'ElectricalSchema') and obj.ElectricalSchema==1


def read_model(obj):
    if not is_sheet(obj):raise ValueError('Objeto nao e uma prancha eletrica.')
    model=json.loads(obj.DrawingJSON)
    model.update(paper=str(obj.Paper),orientation=str(obj.Orientation),grid=obj.Grid.Value)
    model['metadata']={k:str(getattr(obj,prop)) for k,prop in META_PROPS.items()}
    return validate(model)


class ElectricalProxy:
    def execute(self,obj):
        try:
            model=read_model(obj)
            svg=render_svg(model)
            digest=hashlib.sha256(svg.encode('utf-8')).hexdigest()[:24]
            folder=PROJECT/'.runtime/electrical'
            folder.mkdir(parents=True,exist_ok=True)
            path=folder/(digest+'.svg')
            if not path.exists():path.write_text(svg,encoding='utf-8')
            template=obj.Document.getObject(obj.TemplateName)
            if template is not None and str(template.Template)!=str(path):template.Template=str(path)
            obj.SymbolCount=len(model['symbols']);obj.WireCount=len(model['wires']);obj.LastError=''
        except Exception as error:
            obj.LastError=str(error)
            App.Console.PrintError('CESS Eletrica: '+str(error)+'\n')

    def onDocumentRestored(self,obj):obj.touch()
    def dumps(self):return None
    def loads(self,state):pass


class ElectricalViewProvider:
    def getIcon(self):return str(Path(__file__).parent/'icons/electrical.svg')
    def attach(self,view):pass
    def doubleClicked(self,view):
        from cess_gui.electrical_editor import open_editor
        open_editor(view.Object)
        return True
    def dumps(self):return None
    def loads(self,state):pass


def set_properties(obj,model):
    obj.Paper=model['paper'];obj.Orientation=model['orientation'];obj.Grid=model['grid']
    for k,prop in META_PROPS.items():setattr(obj,prop,model['metadata'][k])
    obj.DrawingJSON=json.dumps(model,ensure_ascii=False,separators=(',',':'))


def apply_model(obj,model,transaction='Editar diagrama eletrico'):
    model=validate(model)
    doc=obj.Document;doc.openTransaction(transaction)
    try:
        set_properties(obj,model);doc.recompute()
        if obj.LastError:raise ValueError(obj.LastError)
        doc.commitTransaction()
    except Exception:
        doc.abortTransaction();doc.recompute();raise
    return sheet_info(obj)


def create_sheet(document=None,name='PranchaEletrica',model=None):
    model=validate(model) if model is not None else new_drawing()
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,59}',name):raise ValueError('Nome interno invalido.')
    doc=document or App.ActiveDocument or App.newDocument('ProjetoEletrico')
    if doc.getObject(name):raise ValueError('Nome de prancha ja existe.')
    import TechDraw
    doc.openTransaction('Criar prancha eletrica')
    try:
        obj=doc.addObject('App::FeaturePython',name)
        obj.Label='Eletrica - '+model['metadata']['title']
        obj.addProperty('App::PropertyInteger','ElectricalSchema','CESS');obj.ElectricalSchema=1
        obj.addProperty('App::PropertyEnumeration','Paper','Prancha');obj.Paper=list(PAPERS)
        obj.addProperty('App::PropertyEnumeration','Orientation','Prancha');obj.Orientation=['landscape','portrait']
        obj.addProperty('App::PropertyLength','Grid','Prancha','Grade do editor em mm')
        for key,prop in META_PROPS.items():obj.addProperty('App::PropertyString',prop,'Carimbo',key)
        for prop in ('DrawingJSON','PageName','TemplateName','LastError'):
            obj.addProperty('App::PropertyString',prop,'CESS')
        for prop in ('SymbolCount','WireCount'):obj.addProperty('App::PropertyInteger',prop,'Resultados')
        for prop in ('ElectricalSchema','PageName','TemplateName','LastError','SymbolCount','WireCount'):obj.setEditorMode(prop,1)
        obj.setEditorMode('DrawingJSON',2)
        page=doc.addObject('TechDraw::DrawPage',name+'_Pagina');page.Label='Prancha - '+model['metadata']['title']
        template=doc.addObject('TechDraw::DrawSVGTemplate',name+'_Template')
        template.addProperty('App::PropertyLink','DrawingSource','CESS');template.DrawingSource=obj
        page.Template=template;obj.PageName=page.Name;obj.TemplateName=template.Name
        set_properties(obj,model);obj.Proxy=ElectricalProxy()
        if App.GuiUp:obj.ViewObject.Proxy=ElectricalViewProvider()
        doc.recompute()
        if obj.LastError:raise ValueError(obj.LastError)
        doc.commitTransaction()
    except Exception:
        doc.abortTransaction();raise
    return obj


def sheet_info(obj):
    model=read_model(obj)
    return dict(document=obj.Document.Name,sheet=obj.Name,page=obj.PageName,template=obj.TemplateName,
                paper=model['paper'],orientation=model['orientation'],size_mm=list(dimensions(model)),
                drawing_bounds_mm=list(drawing_bounds(model)),symbol_count=len(model['symbols']),
                wire_count=len(model['wires']),simulation=False,drawing=model)


def export_sheet(obj,path):
    from PySide import QtCore,QtGui,QtSvg
    path=Path(path);model=read_model(obj);svg=render_svg(model)
    if path.suffix.lower()=='.svg':path.write_text(svg,encoding='utf-8')
    elif path.suffix.lower()=='.json':path.write_text(json.dumps(model,ensure_ascii=False,indent=2),encoding='utf-8')
    else:
        renderer=QtSvg.QSvgRenderer(QtCore.QByteArray(svg.encode('utf-8')))
        if not renderer.isValid():raise ValueError('SVG da prancha invalido.')
        w,h=dimensions(model)
        if path.suffix.lower()=='.pdf':
            target=QtGui.QPdfWriter(str(path))
            target.setPageSize(QtGui.QPageSize(QtCore.QSizeF(w,h),QtGui.QPageSize.Millimeter,'CESS '+model['paper']))
            target.setPageMargins(QtCore.QMarginsF(0,0,0,0),QtGui.QPageLayout.Millimeter)
            target.setResolution(300);target.setTitle(model['metadata']['title']);target.setCreator('CESS Eletrica / FreeCAD')
            painter=QtGui.QPainter(target)
            if not painter.isActive():raise ValueError('Nao foi possivel abrir a saida PDF.')
            renderer.render(painter,QtCore.QRectF(0,0,target.width(),target.height()))
            painter.end();del target
        elif path.suffix.lower()=='.png':
            scale=2400/max(w,h);width,height=round(w*scale),round(h*scale)
            image=QtGui.QImage(width,height,QtGui.QImage.Format_ARGB32_Premultiplied);image.fill(QtCore.Qt.white)
            painter=QtGui.QPainter(image);renderer.render(painter,QtCore.QRectF(0,0,width,height));painter.end()
            if not image.save(str(path)):raise ValueError('Falha ao salvar PNG.')
        else:raise ValueError('Extensoes eletricas: .svg, .pdf, .png ou .json.')
    return dict(path=str(path),bytes=path.stat().st_size,paper=model['paper'],size_mm=list(dimensions(model)))
