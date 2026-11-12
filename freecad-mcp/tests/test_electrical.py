from copy import deepcopy
import math
import xml.etree.ElementTree as ET
import pytest
from cess_gui.electrical_model import (PAPERS,new_drawing,validate,dimensions,drawing_bounds,
    add_symbol,add_wire,wire_points,remove_item,pin_position)
from cess_gui.electrical_symbols import CATALOG
from cess_gui.electrical_svg import render_svg,standalone_symbol
from cess_gui.electrical_examples import start_stop_example


@pytest.mark.parametrize('paper',PAPERS)
@pytest.mark.parametrize('orientation',['portrait','landscape'])
def test_paper_margins_titleblock_and_symbols(paper,orientation):
    model=new_drawing(paper,orientation);w,h=dimensions(model)
    assert drawing_bounds(model)==(20,10,w-10,h-50)
    for kind in CATALOG:
      for angle in (0,90,180,270):
        case,item_id=add_symbol(model,kind,60,70,rotation=angle)
        assert len(case['symbols'])==1
        svg=ET.fromstring(render_svg(case))
        assert svg.attrib['width']==str(w)+'mm' and svg.attrib['height']==str(h)+'mm'
        assert len(list(svg.iter('{http://www.w3.org/2000/svg}g')))>0
        ET.fromstring(standalone_symbol(case['symbols'][0]))


def test_terminal_links_follow_move_and_rotation():
    model,a=add_symbol(new_drawing(),'contact_no',60,70,'KM1')
    model,b=add_symbol(model,'coil',60,130,'KM1')
    model,w=add_wire(model,dict(symbol=a,pin='14'),dict(symbol=b,pin='A1'),'1')
    assert wire_points(model,model['wires'][0])==[[60,80],[60,120]]
    model['symbols'][0].update(x=100,rotation=90)
    model=validate(model);pts=wire_points(model,model['wires'][0])
    assert pts[0]==pytest.approx([90,70])
    assert pts[-1]==[60,120]
    assert all(abs(a[0]-b[0])<1e-8 or abs(a[1]-b[1])<1e-8 for a,b in zip(pts,pts[1:]))
    result=remove_item(model,a)
    assert len(result['symbols'])==1 and not result['wires']


def test_crossing_does_not_create_junction_or_simulation():
    model=new_drawing()
    model,_=add_wire(model,dict(point=[40,60]),dict(point=[100,60]))
    model,_=add_wire(model,dict(point=[70,40]),dict(point=[70,90]))
    assert not model['symbols'] and len(model['wires'])==2
    model['simulate']=True
    with pytest.raises(ValueError):validate(model)


@pytest.mark.parametrize('kind,x,y,rotation',[
    ('contact_no',20,50,0),('coil',100,240,0),('coil',410,50,0),('unknown',80,80,0),
    ('coil',80,80,45),('coil',float('nan'),80,0),('coil',True,80,0),
])
def test_reject_margin_titleblock_and_bad_symbols(kind,x,y,rotation):
    with pytest.raises(ValueError):add_symbol(new_drawing(),kind,x,y,rotation=rotation)


def test_reject_dangling_pin_zero_wire_and_unsafe_color():
    model,a=add_symbol(new_drawing(),'contact_no',60,70)
    for start,end,color in [(dict(symbol='Missing',pin='1'),dict(point=[100,100]),'#000000'),
                            (dict(symbol=a,pin='bad'),dict(point=[100,100]),'#000000'),
                            (dict(point=[50,50]),dict(point=[50,50]),'#000000'),
                            (dict(point=[50,50]),dict(point=[100,100]),'url(https://bad)')]:
        with pytest.raises(ValueError):add_wire(model,start,end,color=color)


def test_literal_text_svg_escaping_and_valid_example():
    model=start_stop_example()
    assert len(model['symbols'])==14 and len(model['wires'])==15
    model['metadata']['title']='<script> & "Comando"'
    model['symbols'][0]['tag']='L<&'
    svg=render_svg(model);root=ET.fromstring(svg)
    assert not root.findall('.//{http://www.w3.org/2000/svg}script')
    assert '&lt;script&gt;' in svg and '&amp;' in svg
    assert any('L<&'==element.text for element in root.iter())


@pytest.mark.parametrize('field,value',[('paper','A5'),('paper',[]),('orientation','diagonal'),('version',True),('grid',0)])
def test_invalid_sheet(field,value):
    model=new_drawing();model[field]=value
    with pytest.raises(ValueError):validate(model)


def test_reject_unknown_metadata_and_bad_sheet_count():
    for data in ({'extra':'hidden'},{'sheet':'2','sheets':'1'},{'revision':'r'*13}):
        model=new_drawing();model['metadata'].update(data)
        with pytest.raises(ValueError):validate(model)
