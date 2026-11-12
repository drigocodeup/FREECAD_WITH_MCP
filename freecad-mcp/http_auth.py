"""HTTP authentication: pre-shared bearer or external OAuth/JWKS verification."""
import secrets
import anyio
import jwt
from mcp.server.auth.provider import AccessToken
from starlette.responses import JSONResponse


class BearerGate:
    def __init__(self, app, token):
        self.app,self.expected = app,token.encode('ascii')

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            await self.app(scope,receive,send)
            return
        values = [value for key,value in scope.get('headers',[]) if key.lower()==b'authorization']
        valid = False
        if len(values)==1:
            scheme,separator,credential = values[0].partition(b' ')
            valid = scheme.lower()==b'bearer' and bool(separator) and secrets.compare_digest(credential,self.expected)
        if not valid:
            response = JSONResponse({'error':'unauthorized'},status_code=401,
                                    headers={'WWW-Authenticate':'Bearer realm="freecad-mcp"','Cache-Control':'no-store'})
            await response(scope,receive,send)
            return
        await self.app(scope,receive,send)


class OAuthJWTVerifier:
    def __init__(self, settings, jwk_client=None):
        self.settings = settings
        self.jwk_client = jwk_client or jwt.PyJWKClient(settings.jwks_url,cache_keys=True,timeout=5)

    def _verify(self, token):
        if len(token)>16384:
            return None
        algorithm = jwt.get_unverified_header(token).get('alg')
        if algorithm not in ('RS256','ES256'):
            return None
        key = self.jwk_client.get_signing_key_from_jwt(token).key
        claims = jwt.decode(token,key,algorithms=['RS256','ES256'],audience=self.settings.audience,
                            issuer=self.settings.issuer,leeway=10,
                            options={'require':['exp','iat','iss','aud','sub']})
        scope = claims.get('scope',claims.get('scp',[]))
        scopes = scope.split() if isinstance(scope,str) else scope
        if not isinstance(scopes,list) or not all(isinstance(s,str) for s in scopes):
            return None
        client = claims.get('azp',claims.get('client_id',claims['sub']))
        if not isinstance(client,str):
            return None
        return AccessToken(token=token,client_id=client,subject=claims['sub'],scopes=scopes,
                           expires_at=int(claims['exp']),resource=self.settings.resource_url,claims=claims)

    async def verify_token(self, token):
        try:
            return await anyio.to_thread.run_sync(self._verify,token)
        except (jwt.PyJWTError,ValueError,TypeError,KeyError,OSError):
            # Fail closed, including JWKS network failures. Never log the token.
            return None
