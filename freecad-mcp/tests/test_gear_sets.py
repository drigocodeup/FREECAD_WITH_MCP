import pytest
from cess_gui.generator_specs import validate
from cess_gui.gear_sets import gear_pair_layout


def layout(**values):
    return gear_pair_layout(validate('gear_pair',values))


def test_reduction_and_increase():
    a,b = layout(ratio='2:1'),layout(ratio='1:2')
    assert (a['input_teeth'],a['output_teeth'])==(20,40)
    assert (b['input_teeth'],b['output_teeth'])==(40,20)
    assert a['speed_multiplier']==-.5 and b['speed_multiplier']==-2
    assert a['center_distance']==60.1 and a['contact_ratio']>1
    assert a['output_angle']==pytest.approx(4.5)


def test_exact_fraction_and_phase():
    a = layout(ratio='1,5 : 1',input_angle=9)
    assert a['ratio']=='3:2'
    assert a['input_teeth']==20 and a['output_teeth']==30
    # z1*theta1 + z2*theta2 == z2*180-180 (mod 360).
    assert (20*9+30*a['output_angle']-(30*180-180)) % 360 == pytest.approx(0)


@pytest.mark.parametrize('values',[
    {'ratio':'0:1'},{'ratio':'2'},{'ratio':'-1:2'},{'ratio':'__import__("os")'},
    {'ratio':'100:1'},{'ratio':'1e3:1'},{'ratio':'1/2:1'},
    {'shaft_diameter':100},{'shaft_extension':3},{'center_clearance':2,'module':.3},
])
def test_rejected_before_cad(values):
    with pytest.raises(ValueError): layout(**values)


def test_equal_and_undercut_threshold():
    assert layout(ratio='10:10')['ratio']=='1:1'
    assert layout(pressure_angle=14.5)['input_teeth']>=32
    assert layout(make_housing=False,shaft_extension=3)['center_distance']>0
