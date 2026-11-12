"""Authenticated Streamable HTTP entry point using the official MCP SDK."""
import logging
import sys
import uvicorn
from mcp.server.auth.settings import AuthSettings
from mcp.server.transport_security import TransportSecuritySettings
from application import create_server
from http_config import HTTPConfig
from http_auth import BearerGate, OAuthJWTVerifier


def create_http_app(config=None, token_verifier=None):
    config = config or HTTPConfig.from_env()
    settings = dict(host=config.host,port=config.port,stateless_http=True,json_response=True,
                    max_request_body_size=65536,
                    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=True,
                        allowed_hosts=list(config.allowed_hosts),allowed_origins=list(config.allowed_origins)))
    if config.auth_mode == 'oauth':
        settings['auth'] = AuthSettings(issuer_url=config.issuer,resource_server_url=config.resource_url,
                                       required_scopes=list(config.scopes),validate_token_resource=True)
        settings['token_verifier'] = token_verifier or OAuthJWTVerifier(config)
    server = create_server(**settings)
    app = server.streamable_http_app()
    if config.auth_mode == 'bearer':
        app = BearerGate(app,config.token)
    return app


def main():
    logging.basicConfig(stream=sys.stderr,level=logging.INFO)
    try:
        config = HTTPConfig.from_env()
    except ValueError as error:
        logging.error('Configuracao HTTP invalida: %s',error)
        return 2
    logging.info('FreeCAD MCP Streamable HTTP: %s; auth=%s; sem exposicao automatica.',config.url,config.auth_mode)
    uvicorn.run(create_http_app(config),host=config.host,port=config.port,
                access_log=False,proxy_headers=False,log_level='info')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
