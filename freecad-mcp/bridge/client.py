import json
import socket
import time
import uuid
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]


def call(operation, params=None, timeout=30):
    endpoint = PROJECT / '.runtime/endpoint.json'
    if not endpoint.exists():
        raise RuntimeError('Bridge indisponivel. Execute scripts/start.ps1 ou carregue a macro no FreeCAD aberto.')
    info = json.loads(endpoint.read_text(encoding='utf-8'))
    request_id = str(uuid.uuid4())
    request = {'id': request_id, 'token': info['token'], 'operation': operation,
               'params': params or {}, 'deadline': time.time() + timeout}
    try:
        with socket.create_connection(('127.0.0.1', info['port']), timeout=timeout) as s:
            s.settimeout(timeout)
            s.sendall((json.dumps(request, allow_nan=False) + '\n').encode('utf-8'))
            data = bytearray()
            while b'\n' not in data:
                chunk = s.recv(65536)
                if not chunk:
                    raise RuntimeError('Bridge encerrou sem resposta')
                data.extend(chunk)
                if len(data) > 4 * 1024 * 1024:
                    raise RuntimeError('Resposta excede 4 MiB')
        response = json.loads(data)
    except TimeoutError as exc:
        raise RuntimeError('Timeout: resultado CAD pode ter sido aplicado. Inspecione o documento antes de repetir.') from exc
    if response.get('id') != request_id:
        raise RuntimeError('ID da resposta difere da requisicao')
    if not response.get('ok'):
        raise ValueError(response['error']['message'])
    return response['result']
