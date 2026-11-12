"""Authenticated loopback JSON transport, dispatched on Qt's GUI thread."""
import json
import os
import secrets
import time
from pathlib import Path
from PySide import QtCore, QtNetwork
from bridge.operations import Operations

INSTANCE = None
MAX_BYTES = 65536


class Bridge(QtCore.QObject):
    def __init__(self, project):
        super().__init__()
        self.project = Path(project).resolve()
        self.runtime = self.project / '.runtime'
        self.runtime.mkdir(exist_ok=True)
        settings = json.loads((self.project / 'config/settings.json').read_text(encoding='utf-8'))
        self.ops = Operations((self.project / settings['models_directory']).resolve())
        self.token = secrets.token_urlsafe(48)
        self.server = QtNetwork.QTcpServer(self)
        self.buffers = {}
        self.completed = {}
        if not self.server.listen(QtNetwork.QHostAddress('127.0.0.1'), 0):
            raise RuntimeError(self.server.errorString())
        self.server.newConnection.connect(self.accept)
        endpoint = {'port': self.server.serverPort(), 'token': self.token, 'pid': os.getpid()}
        temp = self.runtime / 'endpoint.tmp'
        temp.write_text(json.dumps(endpoint), encoding='utf-8')
        os.replace(temp, self.runtime / 'endpoint.json')

    def accept(self):
        while self.server.hasPendingConnections():
            s = self.server.nextPendingConnection()
            if len(self.buffers) >= 16:
                s.abort()
                s.deleteLater()
                continue
            self.buffers[s] = bytearray()
            s.readyRead.connect(lambda s=s: self.read(s))
            s.disconnected.connect(lambda s=s: self.cleanup(s))
            timer = QtCore.QTimer(s)
            timer.setSingleShot(True)
            timer.timeout.connect(s.abort)
            timer.start(10000)
            if s.bytesAvailable():
                self.read(s)

    def cleanup(self, s):
        self.buffers.pop(s, None)
        s.deleteLater()

    def read(self, s):
        buf = self.buffers.get(s)
        if buf is None:
            return
        buf.extend(bytes(s.readAll()))
        if len(buf) > MAX_BYTES:
            s.abort()
            return
        if b'\n' not in buf:
            return
        request_id = None
        try:
            req = json.loads(bytes(buf).decode('utf-8'))
            if not isinstance(req, dict) or not secrets.compare_digest(str(req.get('token', '')), self.token):
                raise ValueError('Autenticacao invalida')
            request_id = req.get('id')
            if not isinstance(request_id, str) or not 1 <= len(request_id) <= 64:
                raise ValueError('ID invalido')
            if request_id in self.completed:
                response = self.completed[request_id]
            else:
                deadline = req.get('deadline')
                if not isinstance(deadline, (int, float)) or not time.time() < deadline <= time.time() + 120:
                    raise ValueError('Requisicao expirada ou prazo invalido')
                params = req.get('params', {})
                if not isinstance(params, dict):
                    raise ValueError('params deve ser objeto')
                if req.get('operation') == 'shutdown_bridge':
                    result = {'stopped': True}
                    QtCore.QTimer.singleShot(100, self.stop)
                else:
                    result = self.ops.dispatch(req.get('operation'), params)
                response = {'id': request_id, 'ok': True, 'result': result}
                self.completed[request_id] = response
                if len(self.completed) > 128:
                    self.completed.pop(next(iter(self.completed)))
        except Exception as exc:
            response = {'id': request_id, 'ok': False,
                        'error': {'type': type(exc).__name__, 'message': str(exc)}}
        s.write((json.dumps(response, allow_nan=False) + '\n').encode('utf-8'))
        s.disconnectFromHost()

    def stop(self):
        self.server.close()
        endpoint = self.runtime / 'endpoint.json'
        if endpoint.exists():
            saved = json.loads(endpoint.read_text(encoding='utf-8'))
            if saved.get('token') == self.token:
                endpoint.unlink()


def start(project):
    global INSTANCE
    if INSTANCE is not None:
        return INSTANCE
    INSTANCE = Bridge(project)
    import FreeCADGui
    FreeCADGui.getMainWindow().show()
    return INSTANCE
