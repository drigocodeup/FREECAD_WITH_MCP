import pytest
from cess_gui.generator_specs import validate


@pytest.mark.parametrize('params',[
    {'head_type':'torx'},{'diameter':3,'pitch':2},{'pitch':.25,'length':30},
    {'head_size':8},{'nut_size':9},{'socket_depth':8},{'socket_size':13},
    {'left_hand':'yes'},{'length':3,'pitch':2},{'nut_height':1},
])
def test_reject_invalid_fasteners(params):
    with pytest.raises(ValueError): validate('fastener',params)


def test_both_heads_and_socket_only_applies_to_allen():
    assert validate('fastener',{})['head_type']=='allen'
    assert validate('fastener',{'head_type':'sextavada','socket_depth':30})['head_type']=='sextavada'
