import math
import pytest
from bridge.geometry import number, vector, safe_path


@pytest.mark.parametrize('value', [float('nan'), float('inf'), -1, 0, True, '1'])
def test_reject_invalid_dimensions(value):
    with pytest.raises(ValueError):
        number(value, 'length', positive=True)


@pytest.mark.parametrize('filename', ['../escape.FCStd', 'a.step', '', 'sub/../../escape.FCStd'])
def test_path_confinement(tmp_path, filename):
    with pytest.raises(ValueError):
        safe_path(tmp_path, filename, '.FCStd')


def test_symlink_escape(tmp_path):
    outside = tmp_path.parent / 'outside'
    outside.mkdir(exist_ok=True)
    try:
        (tmp_path / 'link').symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip('Windows symlink privilege unavailable')
    with pytest.raises(ValueError):
        safe_path(tmp_path, 'link/model.FCStd', '.FCStd')


def test_vector_and_volume():
    assert vector([1, 2, 3]) == [1., 2., 3.]
    with pytest.raises(ValueError):
        vector([1, 2])
    assert 100 * 60 * 20 - math.pi * 8**2 * 20 == pytest.approx(115978.76140340506)
