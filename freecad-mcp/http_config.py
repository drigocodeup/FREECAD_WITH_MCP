"""Fail-closed HTTP configuration. No credential values are logged."""
from dataclasses import dataclass, field
import ipaddress
import os
from urllib.parse import urlsplit


def loopback(host):
    if host.lower() == 'localhost':
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def https_url(value, name):
    parsed = urlsplit(value)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.fragment or parsed.query:
        raise ValueError(name + ' deve ser uma URL HTTPS, sem credenciais, query ou fragmento.')
    return value


def csv(value):
    return tuple(dict.fromkeys(x.strip() for x in value.split(',') if x.strip()))


@dataclass(frozen=True)
class HTTPConfig:
    host: str
    port: int
    auth_mode: str
    token: str = field(repr=False)
    allowed_hosts: tuple[str,...]
    allowed_origins: tuple[str,...]
    issuer: str = ''
    jwks_url: str = ''
    resource_url: str = ''
    audience: str = ''
    scopes: tuple[str,...] = ('freecad:control',)

    @property
    def url(self):
        host = '['+self.host+']' if ':' in self.host else self.host
        return f'http://{host}:{self.port}/mcp'

    @classmethod
    def from_env(cls, env=None):
        env = os.environ if env is None else env
        host = env.get('FREECAD_MCP_HOST','127.0.0.1').strip()
        if not host or any(c in host for c in '/\\@ \t\r\n'):
            raise ValueError('FREECAD_MCP_HOST invalido.')
        if not loopback(host) and env.get('FREECAD_MCP_ALLOW_NON_LOOPBACK') != '1':
            raise ValueError('Endereco nao local exige FREECAD_MCP_ALLOW_NON_LOOPBACK=1 explicitamente.')
        try:
            port = int(env.get('FREECAD_MCP_PORT','8765'))
        except ValueError as error:
            raise ValueError('FREECAD_MCP_PORT deve ser inteiro.') from error
        if not 1 <= port <= 65535:
            raise ValueError('FREECAD_MCP_PORT deve estar entre 1 e 65535.')
        mode = env.get('FREECAD_MCP_AUTH_MODE','bearer').lower().strip()
        if mode not in ('bearer','oauth'):
            raise ValueError('FREECAD_MCP_AUTH_MODE deve ser bearer ou oauth; modo sem autenticacao nao e permitido.')
        token = env.get('FREECAD_MCP_TOKEN','') if mode == 'bearer' else ''
        if mode == 'bearer' and (not 32 <= len(token) <= 512 or not token.isascii() or any(c.isspace() for c in token)):
            raise ValueError('Defina FREECAD_MCP_TOKEN com 32 a 512 caracteres ASCII sem espacos; use valor aleatorio.')
        formatted_host = '['+host+']' if ':' in host else host
        hosts = csv(env.get('FREECAD_MCP_ALLOWED_HOSTS',f'127.0.0.1:{port},localhost:{port},[::1]:{port},{formatted_host}:{port}'))
        if not hosts or any('*' in item or any(c in item for c in '/\\@ \t\r\n') for item in hosts):
            raise ValueError('FREECAD_MCP_ALLOWED_HOSTS exige hosts explicitos, sem wildcard ou URL.')
        origins = csv(env.get('FREECAD_MCP_ALLOWED_ORIGINS',f'http://127.0.0.1:{port},http://localhost:{port},http://[::1]:{port}'))
        for origin in origins:
            parsed = urlsplit(origin)
            if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.path or parsed.query or parsed.fragment or parsed.username or parsed.password or '*' in origin:
                raise ValueError('Origins devem ser origens completas e explicitas, sem caminho ou wildcard.')
        kwargs = {}
        if mode == 'oauth':
            kwargs['issuer'] = https_url(env.get('FREECAD_MCP_OAUTH_ISSUER',''),'FREECAD_MCP_OAUTH_ISSUER')
            kwargs['jwks_url'] = https_url(env.get('FREECAD_MCP_OAUTH_JWKS_URL',''),'FREECAD_MCP_OAUTH_JWKS_URL')
            kwargs['resource_url'] = https_url(env.get('FREECAD_MCP_RESOURCE_URL',''),'FREECAD_MCP_RESOURCE_URL')
            kwargs['audience'] = env.get('FREECAD_MCP_OAUTH_AUDIENCE',kwargs['resource_url'])
            kwargs['scopes'] = csv(env.get('FREECAD_MCP_REQUIRED_SCOPES','freecad:control'))
            if not kwargs['audience'] or not kwargs['scopes']:
                raise ValueError('OAuth exige audience e pelo menos um scope.')
        return cls(host,port,mode,token,hosts,origins,**kwargs)
