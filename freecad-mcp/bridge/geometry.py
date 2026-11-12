import math
from pathlib import Path


def number(value, name, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{name}: numero esperado')
    if not math.isfinite(value) or abs(value) > 1e7 or (positive and value <= 0):
        raise ValueError(f'{name}: valor fora do intervalo permitido')
    return float(value)


def vector(value):
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError('Vetor deve conter tres numeros')
    return [number(x, 'coordenada') for x in value]


def safe_path(root, filename, suffix):
    if not isinstance(filename, str) or not filename:
        raise ValueError('Nome de arquivo obrigatorio')
    root = Path(root).resolve()
    path = (root / filename).resolve()
    if not path.is_relative_to(root) or path == root:
        raise ValueError('Arquivo deve estar dentro da pasta modelos autorizada')
    if path.suffix.lower() != suffix.lower():
        raise ValueError(f'Extensao obrigatoria: {suffix}')
    return path


def shape_info(shape):
    if shape.isNull():
        raise ValueError('Geometria vazia')
    b = shape.BoundBox
    return {'valid': bool(shape.isValid()), 'solids': len(shape.Solids),
            'volume_mm3': shape.Volume,
            'bounding_box': {'min': [b.XMin, b.YMin, b.ZMin],
                             'max': [b.XMax, b.YMax, b.ZMax],
                             'size': [b.XLength, b.YLength, b.ZLength]}}
