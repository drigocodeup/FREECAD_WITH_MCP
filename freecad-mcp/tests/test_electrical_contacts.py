"""Contact families preserve independent/common terminals and remain pure 2D."""
import xml.etree.ElementTree as ET
import json
from pathlib import Path
from cess_gui.electrical_symbols import CATALOG,CADE_CONTACTS
from cess_gui.electrical_examples import contacts_catalog_example
from cess_gui.electrical_model import new_drawing,add_symbol,add_wire,wire_points
from cess_gui.electrical_svg import render_svg

def test_audited_contact_commands_and_existing_ids():
    assert len(CADE_CONTACTS)==66 and len(set(CADE_CONTACTS.values()))==66
    assert len(CATALOG)==77
    assert all(s['dimension']=='2D' for s in CATALOG.values())
    assert CADE_CONTACTS[32937]=='contact_no' and CADE_CONTACTS[32915]=='emergency'
    for command,kind in CADE_CONTACTS.items():assert CATALOG[kind]['reference_command']==command
    inventory=json.loads((Path(__file__).resolve().parents[1]/'docs/cadesimu-contacts-inventory.json').read_text(encoding='utf-8'))
    assert set(CADE_CONTACTS)=={i for bar in inventory['scoped_toolbars'] for i in bar['commands']}

def test_independent_and_changeover_contacts_have_different_topologies():
    pair=CATALOG['contact_no_nc']['pins'];change=CATALOG['contact_changeover']['pins']
    assert [p[0] for p in pair]==['13','14','21','22']
    assert [p[0] for p in change]==['11','12','14']
    model,a=add_symbol(new_drawing(),'timer_on_changeover',70,70)
    model,b=add_symbol(model,'thermal_no',70,130)
    model,_=add_wire(model,{'symbol':a,'pin':'14'},{'symbol':b,'pin':'97'})
    assert wire_points(model,model['wires'][0])[0]==[74,80]
    assert wire_points(model,model['wires'][0])[-1]==[70,120]

def test_every_catalog_entry_renders_and_power_pins_are_distinct():
    model=contacts_catalog_example();assert len(model['symbols'])==77
    assert len(model['notes'])==77
    ET.fromstring(render_svg(model))
    for poles in range(1,5):
        pins=CATALOG['power_contactor_'+str(poles)]['pins']
        assert len(pins)==2*poles and len(set(p[0] for p in pins))==2*poles
