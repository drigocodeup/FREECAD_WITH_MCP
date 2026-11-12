"""Original vector symbols for electrical drafting; no simulation state."""

def spec(label,category,prefix,pins,geometry):
    return dict(label=label,category=category,prefix=prefix,pins=pins,geometry=geometry)

LEADS=[('L',0,-10,0,-3),('L',0,3,0,10)]
NO=LEADS+[('L',-1,-3,1,-3),('L',0,3,4,-3)]
NC=LEADS+[('L',0,-3,4,-3),('L',0,3,4,-3)]
PUSH=[('L',-6,-3,-6,3),('D',-6,0,1,0)]
COIL=[('L',0,-10,0,-4),('R',-4,-4,8,8),('L',0,4,0,10)]
CATALOG={
    'contact_no':spec('Contato NA','Contatos','KM',[('13',0,-10),('14',0,10)],NO),
    'contact_nc':spec('Contato NF','Contatos','KM',[('21',0,-10),('22',0,10)],NC),
    'push_no':spec('Botoeira NA (liga)','Comando','S',[('13',0,-10),('14',0,10)],NO+PUSH),
    'push_nc':spec('Botoeira NF (desliga)','Comando','S',[('11',0,-10),('12',0,10)],NC+PUSH),
    'emergency':spec('Emergencia NF','Comando','S',[('11',0,-10),('12',0,10)],NC+PUSH+[('L',-8,-3,-4,-3)]),
    'selector':spec('Seletor NA','Comando','SA',[('13',0,-10),('14',0,10)],NO+[('C',-6,0,2),('L',-6,0,-8,-3),('D',-4,0,1,0)]),
    'coil':spec('Bobina de contator/rele','Bobinas','KM',[('A1',0,-10),('A2',0,10)],COIL),
    'timer_coil':spec('Bobina de temporizador','Bobinas','KT',[('A1',0,-10),('A2',0,10)],COIL+[('T',-1,1,'T',2.5)]),
    'thermal_nc':spec('Contato NF de rele termico','Protecao','F',[('95',0,-10),('96',0,10)],NC+[('T',-7,5,'I>',2)]),
    'fuse':spec('Fusivel','Protecao','F',[('1',0,-10),('2',0,10)],[('L',0,-10,0,-5),('R',-2,-5,4,10),('L',0,-5,0,5),('L',0,5,0,10)]),
    'breaker':spec('Disjuntor unipolar','Protecao','QF',[('1',0,-10),('2',0,10)],NO+[('L',-1,2,1,4),('L',-1,4,1,2)]),
    'lamp':spec('Sinaleiro','Receptores','H',[('X1',0,-10),('X2',0,10)],[('L',0,-10,0,-5),('C',0,0,5),('L',-3.5,-3.5,3.5,3.5),('L',-3.5,3.5,3.5,-3.5),('L',0,5,0,10)]),
    'motor':spec('Motor (representacao)','Receptores','M',[('U1',0,-10),('U2',0,10)],[('L',0,-10,0,-5),('C',0,0,5),('T',-2,1.5,'M',4),('L',0,5,0,10)]),
    'resistor':spec('Resistor','Receptores','R',[('1',0,-10),('2',0,10)],[('L',0,-10,0,-5),('R',-2,-5,4,10),('L',0,5,0,10)]),
    'terminal':spec('Borne / ponto de alimentacao','Conexoes','X',[('1',0,0)],[('C',0,0,1.3)]),
    'junction':spec('Ponto de juncao','Conexoes','',[('1',0,0)],[('F',0,0,.7)]),
    'ground':spec('Terra de protecao','Conexoes','PE',[('PE',0,-10)],[('L',0,-10,0,0),('L',-4,0,4,0),('L',-2.7,2,2.7,2),('L',-1.4,4,1.4,4)]),
}


def catalog():
    return [{'kind':key,**value} for key,value in CATALOG.items()]
