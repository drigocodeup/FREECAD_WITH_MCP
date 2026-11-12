import pytest
from cess_gui.generator_specs import SPECS, defaults, validate


@pytest.mark.parametrize('kind',list(SPECS))
def test_defaults_are_valid(kind):
    assert validate(kind,{}) == validate(kind,defaults(kind))


@pytest.mark.parametrize('kind,params',[
    ('gear',{'teeth':12.5}), ('gear',{'teeth':True}), ('gear',{'bore':100}),
    ('gear',{'module':float('nan')}), ('gear',{'arbitrary_code':'ignored?'}),
    ('box',{'height':5,'floor':5}), ('box',{'length':10,'wall':5}),
    ('box',{'lip_depth':50}), ('box',{'length':10,'width':10,'wall':2,'clearance':2}),
    ('organizer',{'rows':20,'columns':20}), ('organizer',{'rows':20}),
    ('letters',{'text':'ABC123'}), ('letters',{'text':' '}), ('letters',{'text':'A\nB'}),
    ('letters',{'text':'A'*25}), ('letters',{'font_file':'missing.ttf'}),
    ('letters',{'depth':2,'floor':2}), ('letters',{'wall':1,'clearance':1}),
    ('numbers',{'text':'12A'}), ('numbers',{'text':'-1'}), ('numbers',{'make_front':'yes'}),
])
def test_reject_invalid_parameters(kind,params):
    with pytest.raises(ValueError):
        validate(kind,params)


def test_numeric_zero_and_optional_front():
    assert validate('gear',{'bore':0})['bore'] == 0
    assert validate('numbers',{'text':'001 08','clearance':0})['text'] == '001 08'
    assert not validate('letters',{'make_front':False})['make_front']
