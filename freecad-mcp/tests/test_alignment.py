import pytest
from cess_gui.alignment import alignment_delta


def test_center_nested_rectangles():
    # Outer 100x60 at origin; inner 40x20 initially at (70,55).
    assert alignment_delta((90, 65, 7), (50, 30, 0), 'XY') == (-40, -35, 0)
    assert alignment_delta((90, 65, 7), (50, 30, 0), 'X') == (-40, 0, 0)
    assert alignment_delta((90, 65, 7), (50, 30, 0), 'XYZ') == (-40, -35, -7)


@pytest.mark.parametrize('axes,point', [('AB', (1,2,3)), ('XY', (1,2)), ('X', (float('nan'),0,0)), ('XY', (True,0,0))])
def test_reject_unsafe_alignment(axes, point):
    with pytest.raises(ValueError):
        alignment_delta(point, (0,0,0), axes)
