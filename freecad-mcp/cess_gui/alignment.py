"""Geometry-independent validation and translation calculation."""
import math


def alignment_delta(moving_center, reference_center, axes='XY'):
    if axes not in ('X', 'Y', 'Z', 'XY', 'XZ', 'YZ', 'XYZ'):
        raise ValueError('Eixos permitidos: X, Y, Z, XY, XZ, YZ ou XYZ.')
    points = []
    for point in (moving_center, reference_center):
        if len(point) != 3:
            raise ValueError('O centro deve ter tres coordenadas.')
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in point):
            raise ValueError('Coordenadas devem ser numeros finitos.')
        points.append(point)
    return tuple(points[1][i] - points[0][i] if axis in axes else 0.0
                 for i, axis in enumerate('XYZ'))
