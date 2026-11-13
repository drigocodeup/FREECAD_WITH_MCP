"""A drawing example, with no simulated switching or installation design claim."""
from cess_gui.electrical_model import new_drawing,add_symbol,add_wire,validate


def start_stop_example():
    model=new_drawing(metadata={'company':'SENAI / CESS','title':'Comando de contator - partida e parada com selo',
                                'project':'ELE-001','author':'','revision':'0'})
    ids={}
    for key,kind,x,y,tag,desc in [
        ('source','terminal',60,35,'L+','24 Vcc'),('fuse','fuse',60,55,'F1','Protecao'),
        ('stop','push_nc',60,85,'S0','Desliga'),('j1','junction',60,110,'',''),('j2','junction',100,110,'',''),
        ('start','push_no',60,135,'S1','Liga'),('seal','contact_no',100,135,'KM1','Selo'),
        ('j3','junction',60,160,'',''),('j4','junction',100,160,'',''),('j5','junction',140,160,'',''),
        ('coil','coil',60,185,'KM1','Contator'),('lamp','lamp',140,185,'H1','Ligado'),
        ('j6','junction',140,215,'',''),('return','terminal',60,215,'0V','Retorno')]:
        model,ids[key]=add_symbol(model,kind,x,y,tag,description=desc)
    links=[('source','1','fuse','1'),('fuse','2','stop','11'),('stop','12','j1','1'),
           ('j1','1','start','13'),('j1','1','j2','1'),('j2','1','seal','13'),
           ('start','14','j3','1'),('seal','14','j4','1'),('j3','1','j4','1'),
           ('j4','1','j5','1'),('j3','1','coil','A1'),('j5','1','lamp','X1'),
           ('coil','A2','return','1'),('lamp','X2','j6','1'),('return','1','j6','1')]
    for i,(a,ap,b,bp) in enumerate(links):
        model,_=add_wire(model,{'symbol':ids[a],'pin':ap},{'symbol':ids[b],'pin':bp},str(i+1))
    model['notes']=[dict(id='N1',text='COMANDO DE CONTATOR\nPartida, parada e contato de selo',x=195,y=45,size=3),
                    dict(id='N2',text='S0 - Botoeira normalmente fechada\nS1 - Botoeira normalmente aberta\nKM1 - Bobina e contato auxiliar\nH1 - Sinaleiro',x=195,y=75,size=2.5)]
    return validate(model)
def contacts_catalog_example():
    """A0 vector catalog: every symbol and every connectable pin, without solids."""
    import textwrap
    from cess_gui.electrical_symbols import CATALOG
    from cess_gui.electrical_model import new_drawing,add_symbol,validate
    model=new_drawing('A0','landscape',{'company':'CESS','title':'Biblioteca de contatos 2D',
                                      'project':'CAT-CONTATOS','revision':'1'})
    for i,(kind,symbol) in enumerate(CATALOG.items()):
        x=60+(i%9)*120;y=65+(i//9)*85
        tag=str(symbol.get('reference_command','')) or symbol['prefix']+str(i+1)
        model,_=add_symbol(model,kind,x,y,tag=tag)
        model['notes'].append(dict(id='Legenda'+str(i+1),text=textwrap.fill(symbol['label'],32),x=x-15,y=y+18,size=2))
    return validate(model)
