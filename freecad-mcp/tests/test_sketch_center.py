from cess_gui.sketch_center import rectangle_groups

def rectangle(start,x,y,w,h):
    points=[(x,y),(x+w,y),(x+w,y+h),(x,y+h)]
    return [(start+i,points[i],points[(i+1)%4]) for i in range(4)]

def test_nested_rectangles_sharing_a_corner():
    groups=rectangle_groups(rectangle(0,20,20,50,50)+rectangle(5,20,30,40,40))
    assert len(groups)==2
    assert groups[0]['edges']==[5,6,7,8] and groups[0]['size']==(40,40)
    assert groups[1]['edges']==[0,1,2,3] and groups[1]['center']==(45,45)

def test_ignores_open_contour_and_diagonal():
    assert rectangle_groups(rectangle(0,0,0,10,10)[:3])==[]
    assert len(rectangle_groups(rectangle(0,0,0,10,10)+[(8,(0,0),(10,10))]))==1
    assert rectangle_groups([(0,(0,1),(1,0)),(1,(1,0),(2,1)),(2,(2,1),(1,2)),(3,(1,2),(0,1))])==[]

def test_close_endpoints_and_rectangle_with_negative_coordinates():
    segments=rectangle(0,-40,-20,30,10)
    segments[0]=(0,(-40,-20),(-10.0000001,-20))
    groups=rectangle_groups(segments)
    assert len(groups)==1 and groups[0]['bounds']==(-40,-20,-10,-10)
