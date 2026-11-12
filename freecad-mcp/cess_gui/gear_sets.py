"""Two-shaft transmission layout; pure calculations shared by UI and CAD."""
from fractions import Fraction
import math
import re


def gear_pair_layout(p):
    text = p['ratio'].strip().replace(',', '.')
    if len(text)>40 or not re.fullmatch(r'\d+(?:\.\d+)?\s*:\s*\d+(?:\.\d+)?',text):
        raise ValueError('Relacao: use voltas entrada:saida, por exemplo 2:1 ou 1:2.')
    left,right = (Fraction(part.strip()) for part in text.split(':'))
    if left<=0 or right<=0:
        raise ValueError('Os dois valores da relacao devem ser maiores que zero.')
    ratio = left/right
    x,y = ratio.numerator,ratio.denominator
    pressure = math.radians(p['pressure_angle'])
    # Conservative standard full-depth, unshifted involute undercut threshold.
    minimum = max(p['minimum_teeth'],math.ceil(2/math.sin(pressure)**2))
    factor = (minimum+min(x,y)-1)//min(x,y)
    z1,z2 = y*factor,x*factor
    if max(z1,z2)>150:
        raise ValueError('Relacao exige mais de 150 dentes por engrenagem nesta etapa. Reduza a relacao ou o minimo de dentes; relacoes grandes precisam de varias etapas.')
    m = p['module']
    bore = p['shaft_diameter']+p['bore_clearance']
    if bore >= m*(min(z1,z2)-4.5):
        raise ValueError('Eixo/furo grande demais para a menor engrenagem. Aumente modulo ou minimo de dentes.')
    r1,r2 = m*z1/2,m*z2/2
    nominal = r1+r2
    distance = nominal+p['center_clearance']
    working_angle = math.acos(nominal*math.cos(pressure)/distance)
    base1,base2 = r1*math.cos(pressure),r2*math.cos(pressure)
    contact = (math.sqrt((r1+m)**2-base1**2)+math.sqrt((r2+m)**2-base2**2)
               -distance*math.sin(working_angle))/(math.pi*m*math.cos(pressure))
    if contact<=1:
        raise ValueError('Folga entre eixos excessiva: razao de contato calculada deve superar 1.')
    if p['make_housing'] and p['shaft_extension'] <= p['housing_wall']+p['axial_clearance']+2:
        raise ValueError('Prolongamento do eixo deve superar parede + folga axial + 2 mm.')
    mode = 'Reducao' if x>y else ('Aumento' if x<y else 'Transmissao 1:1')
    return dict(input_teeth=z1,output_teeth=z2,ratio=f'{x}:{y}',mode=mode,
                speed_multiplier=-float(right/left),center_distance=distance,
                nominal_center_distance=nominal,input_pitch_diameter=2*r1,output_pitch_diameter=2*r2,
                input_tip_radius=r1+m,output_tip_radius=r2+m,bore=bore,
                input_angle=p['input_angle'],
                output_angle=(180-(180+z1*p['input_angle'])/z2) % (360/z2),
                contact_ratio=contact)
