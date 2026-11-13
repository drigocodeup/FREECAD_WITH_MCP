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


def shifted(geometry,x):
    result=[]
    for kind,*v in geometry:
        if kind in ('L','D'):v=[v[0]+x,v[1],v[2]+x,v[3]]
        else:v[0]+=x
        result.append((kind,*v))
    return result


def contact(mode):
    """Independent NA+NF has four pins; changeover has one common and three pins."""
    if mode=='no':return [('13',0,-10),('14',0,10)],list(NO)
    if mode=='nc':return [('21',0,-10),('22',0,10)],list(NC)
    if mode=='no_nc':
        return [('13',-4,-10),('14',-4,10),('21',3,-10),('22',3,10)],shifted(NO,-4)+shifted(NC,3)+[('D',-4,0,3,0)]
    return [('11',0,-10),('12',-4,10),('14',4,10)],[
        ('L',0,-10,0,-3),('L',0,-3,-4,3),('L',-4,3,-4,10),('L',4,3,4,10),('L',3,3,5,3)]


# Command IDs audited from the local CADe_SIMU PE string resources.
# These are independent vector representations, not executable/binary assets.
CADE_CONTACTS={32937:'contact_no',32938:'contact_nc',32909:'push_no',32910:'push_nc',
               32915:'emergency',32928:'thermal_nc'}
MODES=[('no','NA'),('nc','NF'),('no_nc','NA + NF'),('changeover','Comutador')]
FAMILIES=[
    ('contact','Contato auxiliar','Contatos','KM',[32937,32938,32939,32940],[]),
    ('push','Botoeira','Comando','S',[32909,32910,32912,32913],PUSH),
    ('mushroom','Botoeira cogumelo','Comando','S',[32914,32915,32917,32918],PUSH+[('L',-8,-3,-4,-3)]),
    ('switch','Interruptor','Interruptores','SA',[32919,32920,32921,32922],[('D',-7,0,-1,0),('L',-7,0,-5,-4)]),
    ('limit','Fim de curso','Fim de curso','SQ',[32923,32924,32925,32926],[('C',-6,-2,1.5),('L',-6,-.5,-3,2),('D',-3,2,1,2)]),
    ('thermal','Contato de rele termico','Protecao','F',[32927,32928,32929,32930],[('T',-8,-5,'I>',2)]),
    ('timer_on','Temporizado na energizacao','Temporizados','KT',[32933,32934,32935,32936],[('T',-8,-5,'t+',2)]),
    ('timer_off','Temporizado na desenergizacao','Temporizados','KT',[32941,32942,32943,32944],[('T',-8,-5,'t-',2)]),
    ('timer_on_off','Temporizado na energizacao/desenergizacao','Temporizados','KT',[32945,32946,32947,32948],[('T',-8,-5,'t+/-',1.7)]),
]
for family,label,category,prefix,commands,actuator in FAMILIES:
    for (mode,suffix),command in zip(MODES,commands):
        key=CADE_CONTACTS.get(command,family+'_'+mode)
        if key not in CATALOG:
            pins,geometry=contact(mode)
            if family=='thermal':
                pins=[({'13':'97','14':'98','21':'95','22':'96','11':'95','12':'96'}.get(pin,pin),x,y) for pin,x,y in pins]
            CATALOG[key]=spec(label+' '+suffix,category,prefix,pins,geometry+actuator)
        CADE_CONTACTS[command]=key

for family,label,commands,mark in [
    ('inductive','Sensor indutivo',[33032,33020],'L'),
    ('capacitive','Sensor capacitivo',[33021,33022],'C'),
    ('magnetic','Sensor magnetico',[33023,33024],'M'),
    ('pressure','Pressostato',[33253,33254],'P'),
    ('thermostat','Termostato',[33346,33347],'T'),
    ('vacuum','Vacuostato',[33255,33256],'V'),
    ('photoelectric','Barreira fotoeletrica',[33025],'FE'),
    ('photo_receiver','Receptor fotoeletrico',[33034,33033],'RX'),
    ('photo_emitter','Emissor fotoeletrico',[33027],'TX'),
]:
    for (mode,suffix),command in zip(MODES,commands):
        pins,geometry=contact(mode);key=family+'_'+mode
        CATALOG[key]=spec(label+' '+suffix,'Sensores','B',pins,geometry+[('R',-8,-7,4,4),('T',-7.8,-4.3,mark,1.5),('D',-6,-3,0,0)])
        CADE_CONTACTS[command]=key

CATALOG['photo_emitter_no']=spec('Emissor fotoeletrico','Sensores','B',
                                [('A1',0,-10),('A2',0,10)],COIL+[('T',-2,1,'TX',2.5)])

for poles,command in [(1,32899),(2,32834),(3,32833),(4,32835)]:
    pins=[];geometry=[]
    for i in range(poles):
        x=(i-(poles-1)/2)*3
        pins.extend([(str(i*2+1),x,-10),(str(i*2+2),x,10)])
        geometry.extend(shifted(NO,x))
    if poles>1:geometry.append(('D',-(poles-1)*1.5,0,(poles-1)*1.5,0))
    key='power_contactor_'+str(poles)
    CATALOG[key]=spec('Contator de potencia '+str(poles)+' polo(s)','Potencia','KM',pins,geometry)
    CADE_CONTACTS[command]=key

for poles,command in [(1,32900),(2,32836),(3,32837),(4,32838),(3,33219)]:
    is_contactor=command==33219;pins=[];geometry=[]
    for i in range(poles):
        x=(i-(poles-1)/2)*3
        pins.extend([(str(i*2+1),x,-10),(str(i*2+2),x,10)])
        geometry.extend(shifted(NC if is_contactor else NO,x))
    if poles>1:geometry.append(('D',-(poles-1)*1.5,0,(poles-1)*1.5,0))
    key='power_contactor_3_nc' if is_contactor else 'power_switch_'+str(poles)
    if not is_contactor:geometry+=[('L',-8,-3,-6,0),('D',-6,0,0,0)]
    CATALOG[key]=spec('Contator tripolar NF' if is_contactor else 'Interruptor de potencia '+str(poles)+' polo(s)',
                      'Potencia','KM' if is_contactor else 'QS',pins,geometry)
    CADE_CONTACTS[command]=key

for command,key,label,pins,geometry in [
    (33047,'selector_i_0_ii','Seletor I-0-II',[('11',0,-10),('12',-4,10),('14',4,10)],
     [('L',0,-10,0,-3),('L',0,-3,0,1),('L',-4,3,-4,10),('L',4,3,4,10),('T',-8,-5,'0',2)]),
    (33048,'selector_i_ii_iii','Seletor I-II-III',[('11',0,-10),('12',-4,10),('14',0,10),('16',4,10)],
     [('L',0,-10,0,-3),('L',0,-3,-4,3),('L',-4,3,-4,10),('L',0,3,0,10),('L',4,3,4,10)]),
    (33049,'crossover','Comutador de cruzamento',[('1',-4,-10),('2',4,-10),('3',-4,10),('4',4,10)],
     [('L',-4,-10,-4,-4),('L',4,-10,4,-4),('L',-4,-4,4,4),('L',4,-4,-4,4),('L',-4,4,-4,10),('L',4,4,4,10)]),
    (33278,'push_actuator','Acionador de botoeira (2D)',[],[('C',0,0,4),('C',0,0,2.5)]),
    (33392,'mechanical_interlock','Intertravamento mecanico',[],[('D',-8,0,-2,0),('D',2,0,8,0),
      ('L',-2,-2,2,-2),('L',2,-2,0,2),('L',0,2,-2,-2)]),
]:
    CATALOG[key]=spec(label,'Acionamentos','S',pins,geometry)
    CADE_CONTACTS[command]=key

for command,key in CADE_CONTACTS.items():
    CATALOG[key]['reference_command']=command
for item in CATALOG.values():item['dimension']='2D'


def catalog():
    return [{'kind':key,**value} for key,value in CATALOG.items()]
