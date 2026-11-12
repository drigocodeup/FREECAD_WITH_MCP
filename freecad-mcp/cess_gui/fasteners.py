"""Printable bolt/nut pair with a genuine swept 60-degree helical thread."""
import math
import FreeCAD as App
import Part


def hex_prism(across_flats,height,z=0):
    radius=across_flats/math.sqrt(3)
    points=[App.Vector(radius*math.cos(i*math.pi/3),radius*math.sin(i*math.pi/3),z) for i in range(6)]
    wire=Part.makePolygon(points+[points[0]])
    return Part.Face(Part.Wire(wire.Edges)).extrude(App.Vector(0,0,height))


def threaded_rod(radius,length,pitch,left_hand=False):
    # Flat-root prototype profile: 60 degree flanks, P/8 crest, P/6 groove root.
    # This is not a tolerance-class-certified ISO fastener.
    depth=17*math.sqrt(3)*pitch/48
    epsilon=min(.02,pitch/50)
    half_outer=7*pitch/16+epsilon/math.sqrt(3)
    half_root=pitch/12
    z=-pitch
    points=[App.Vector(radius+epsilon,0,z-half_outer),
            App.Vector(radius-depth,0,z-half_root),
            App.Vector(radius-depth,0,z+half_root),
            App.Vector(radius+epsilon,0,z+half_outer)]
    profile=Part.Wire(Part.makePolygon(points+[points[0]]).Edges)
    helix=Part.makeLongHelix(pitch,length+2*pitch,radius,0,left_hand)
    helix.translate(App.Vector(0,0,-pitch))
    cutter=Part.Wire(helix.Edges).makePipeShell([profile],True,True)
    cylinder=Part.makeCylinder(radius,length)
    # Keep the cylinder seam away from the helix start for reliable OCCT cuts.
    cylinder.rotate(App.Vector(),App.Vector(0,0,1),123)
    return cylinder.cut(cutter).removeSplitter()


def build_fasteners(p):
    radius=p['diameter']/2
    shaft=threaded_rod(radius,p['length'],p['pitch'],p['left_hand'])
    if p['head_type']=='allen':
        head=Part.makeCylinder(p['head_size']/2,p['head_height'],App.Vector(0,0,p['length']))
        socket=hex_prism(p['socket_size'],p['socket_depth']+1,
                         p['length']+p['head_height']-p['socket_depth'])
        head=head.cut(socket)
    else:
        head=hex_prism(p['head_size'],p['head_height'],p['length'])
    bolt=shaft.fuse(head).removeSplitter()
    # Enlarge the matching male profile radially by half the diametral allowance.
    tap=threaded_rod(radius+p['clearance']/2,p['nut_height'],p['pitch'],p['left_hand'])
    nut=hex_prism(p['nut_size'],p['nut_height']).cut(tap).removeSplitter()
    nut.translate(App.Vector((p['head_size']+p['nut_size'])/2+10,0,0))
    return {'Parafuso':bolt,'Porca':nut}
