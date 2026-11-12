# Codex local e ChatGPT Web

Os dois servidores usam `application.create_server()` e as mesmas 43 ferramentas, esquemas, validações e bridge Qt. `server.py` continua sendo a entrada STDIO existente. `server_http.py` usa Streamable HTTP do SDK oficial `mcp` 1.x, com respostas JSON e sessões sem estado. O estado dos documentos permanece no FreeCAD gráfico.

## Instalar e iniciar o FreeCAD

Na raiz da sua cópia do repositório:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\freecad-mcp\scripts\install.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\freecad-mcp\scripts\start.ps1
```

Confira `freecad-mcp/config/settings.json`. Se o FreeCAD já estiver aberto sem bridge, execute a macro indicada pelo script no menu Macro. Não inicie dois bridges para a mesma pasta. A instalação do servidor é separada do Python embarcado do FreeCAD.

## Codex no VS Code: STDIO

O registro antigo permanece válido. Para uma instalação nova:

```powershell
$McpProject = (Resolve-Path .\freecad-mcp).Path
codex mcp add freecad_local -- "$McpProject\.venv\Scripts\python.exe" "$McpProject\server.py"
codex mcp list
```

Reabra a sessão Codex/VS Code para carregar o catálogo. A alternativa PowerShell é `scripts/start-stdio.ps1`; o script escreve somente o protocolo no stdout. Não inicie esse processo em um terminal e espere que outra sessão se conecte: o cliente MCP deve iniciar o subprocesso STDIO.

Peça ao assistente que consulte `freecad_health_check`, confirme `gui: true` e crie uma peça usando as ferramentas. Toda modelagem continua na thread principal Qt, com operações permitidas; não existe endpoint de execução de Python arbitrário.

## HTTP local autenticado

Em outro terminal, após iniciar o bridge:

```powershell
# Gera um segredo novo; não imprime nem grava o valor.
$TokenBytes = New-Object byte[] 48
$TokenRng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$TokenRng.GetBytes($TokenBytes)
$TokenRng.Dispose()
$env:FREECAD_MCP_TOKEN = [Convert]::ToBase64String($TokenBytes)
$env:FREECAD_MCP_AUTH_MODE = 'bearer'
$env:FREECAD_MCP_HOST = '127.0.0.1'
$env:FREECAD_MCP_PORT = '8765'
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\freecad-mcp\scripts\start-http.ps1
```

Endpoint: `http://127.0.0.1:8765/mcp`. Envie `Authorization: Bearer <segredo>` em cada requisição. O segredo é compartilhado somente por um canal local seguro com o cliente autorizado; não o coloque em mensagens, URLs, argumentos ou arquivos versionados. Para outro processo, use seu gerenciador de segredos para fornecer o mesmo valor no ambiente. Ctrl+C encerra o HTTP e preserva o FreeCAD.

Esse modo Bearer fixo atende clientes capazes de configurar o cabeçalho. A interface de servidores personalizados do ChatGPT documenta OAuth ou ausência de autenticação, e não uma configuração genérica de chave Bearer fixa. Portanto, não trate esse token como uma configuração pronta de autenticação no ChatGPT Web. Para ele, use o túnel STDIO abaixo ou configure OAuth externo para HTTP.

### Variáveis de ambiente

`config/http.env.example` é apenas referência; nenhum arquivo `.env` é carregado automaticamente.

| Variável | Padrão / significado |
|---|---|
| `FREECAD_MCP_HOST` | `127.0.0.1` (loopback) |
| `FREECAD_MCP_PORT` | `8765`, de 1 a 65535 |
| `FREECAD_MCP_AUTH_MODE` | `bearer` ou `oauth`; não há modo anônimo |
| `FREECAD_MCP_TOKEN` | Obrigatório em Bearer, 32–512 caracteres ASCII sem espaços; use segredo aleatório |
| `FREECAD_MCP_ALLOWED_HOSTS` | CSV exato: `127.0.0.1:8765,localhost:8765,[::1]:8765` e host configurado |
| `FREECAD_MCP_ALLOWED_ORIGINS` | CSV exato das origens HTTP loopback correspondentes à porta |
| `FREECAD_MCP_ALLOW_NON_LOOPBACK` | Somente `1` autoriza um bind fora de loopback, explicitamente |
| `FREECAD_MCP_OAUTH_ISSUER` | Em OAuth, emissor HTTPS exato do JWT, incluindo barra final quando existir |
| `FREECAD_MCP_OAUTH_JWKS_URL` | Em OAuth, endpoint HTTPS das chaves públicas do emissor |
| `FREECAD_MCP_RESOURCE_URL` | Em OAuth, URL HTTPS externa do recurso MCP usada na descoberta |
| `FREECAD_MCP_OAUTH_AUDIENCE` | Audience esperada no JWT; padrão igual a `RESOURCE_URL` |
| `FREECAD_MCP_REQUIRED_SCOPES` | CSV de scopes necessários; padrão `freecad:control` |

O SDK bloqueia Host fora da lista (proteção contra DNS rebinding) e Origin fornecida fora da lista. Clientes MCP sem Origin são permitidos quando autenticados. `Origin: null` é rejeitada. Não há wildcard nem CORS permissivo; adicionar uma origem não configura um cliente de navegador. Requisições MCP têm limite de 64 KiB. Proxy headers não são confiados automaticamente. Nunca use Bearer sobre HTTP em uma rede não confiável: mantenha loopback atrás do túnel ou termine TLS em infraestrutura administrada separadamente. Os scripts não publicam o servidor, alteram firewall ou configuram roteador.

## ChatGPT Web com Secure MCP Tunnel

O [Secure MCP Tunnel oficial](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels) usa conexões HTTPS de saída; não requer publicar uma porta de entrada. O projeto não instala, cria, registra ou inicia túneis automaticamente.

Pré-requisitos dependentes da conta:

- A organização na plataforma precisa disponibilizar Tunnels. Criar/editar exige permissões **Read + Manage**; executar/selecionar exige **Read + Use**.
- O túnel deve estar associado à organização e ao workspace ChatGPT corretos.
- O workspace ChatGPT precisa permitir servidores MCP personalizados/plugins e instalação. Essas permissões são independentes das permissões de Tunnels.
- É necessário um `tunnel_id` e uma chave de execução autorizada em `CONTROL_PLANE_API_KEY`.

Consulte seu administrador se a opção não aparecer. Não foi verificado o acesso desta conta. O binário `tunnel-client` não foi encontrado no PATH na validação local. Obtenha a versão apropriada nas [releases oficiais](https://github.com/openai/tunnel-client/releases/latest), confira as instruções da versão e deixe-a no PATH ou defina `FREECAD_TUNNEL_CLIENT` com o caminho absoluto.

Para preparar um perfil STDIO, sem listener HTTP, usando os comandos documentados:

```powershell
$McpProject = (Resolve-Path .\freecad-mcp).Path
tunnel-client help quickstart
# Substitua tunnel_SEU_ID pelo ID real. O caminho com espaços precisa das aspas internas.
$McpCommand = '"' + "$McpProject\.venv\Scripts\python.exe" + '" "' + "$McpProject\server.py" + '"'
tunnel-client init --sample sample_mcp_stdio_local --profile freecad-local --tunnel-id tunnel_SEU_ID --mcp-command $McpCommand
```

Forneça `CONTROL_PLANE_API_KEY` por seu gerenciador de segredos no ambiente local, sem expor o valor. Depois, quando decidir conectar:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\freecad-mcp\scripts\secure-tunnel.ps1 -Action Doctor
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\freecad-mcp\scripts\secure-tunnel.ps1 -Action Run
```

Sem parâmetros, `secure-tunnel.ps1` apenas solicita a ajuda oficial; se o binário estiver ausente, encerra com diagnóstico. `Doctor` e `Run` são ações explícitas que podem acessar a rede. O túnel STDIO utiliza o mesmo servidor local e o controle de acesso do túnel/workspace; não precisa desativar a autenticação HTTP.

No ChatGPT Web: abra **Plugins → + → Add custom MCP server → Tunnel**, selecione/informe o túnel e configure a autenticação aplicável. Para o perfil STDIO protegido pelo túnel, a escolha sem OAuth só deve ser feita dentro dessa conexão autenticada do túnel, conforme as políticas do workspace. Revise as ferramentas, crie o plugin, instale-o e invoque-o na conversa. A navegação pode variar conforme a conta. Não publique esse servidor privado no diretório público.

### Alternativa: HTTP com OAuth externo

O servidor implementa o papel de resource server OAuth do SDK, descoberta de recurso protegido e validação JWT por JWKS. Não implementa um provedor de identidade. Configure no seu provedor HTTPS os clientes OAuth, consentimento, redirecionamentos e emissão de access tokens JWT RS256 ou ES256 com `iss`, `aud`, `sub`, `iat`, `exp` e scope `freecad:control`. Tokens opacos/introspecção não são suportados. O provedor deve oferecer a descoberta/registro de clientes exigidos pelo fluxo escolhido no ChatGPT.

Defina as variáveis OAuth da tabela e execute `start-http.ps1`. O SDK anuncia `/.well-known/oauth-protected-resource/mcp`; não configure uma URL de emissor fictícia. Para conectar pelo túnel em HTTP, a documentação oferece `--mcp-server-url` no lugar de `--mcp-command`; use uma URL local alcançável pelo agente de túnel e siga `tunnel-client help quickstart` da versão instalada. Não foram supostos parâmetros de injeção de Bearer que não estejam documentados. Ajuste as listas exatas de Host/Origin para os valores efetivamente usados no encaminhamento; não use `*` para contornar um erro.

O fluxo de autorização do usuário e o emissor OAuth precisam ser acessíveis pelo navegador/cliente. O túnel MCP não publica automaticamente o provedor OAuth. Um endereço localhost sozinho não permite que a nuvem ChatGPT alcance este computador. Conexão por URL pública exige TLS e infraestrutura configurada manualmente; este projeto não a cria.

Veja também o [guia oficial de servidor MCP personalizado](https://developers.openai.com/api/docs/guides/custom-mcp-server).

## Testes e limites da validação

```powershell
cd freecad-mcp
.\.venv\Scripts\python.exe -m pytest -q
# Requer bridge real aberto; cria e salva peças em modelos.
$env:FREECAD_INTEGRATION = '1'
.\.venv\Scripts\python.exe -m pytest -q --junitxml=transports-test-results.xml
```

`tests/test_http.py` compara o catálogo completo pelo protocolo STDIO e por HTTP TCP real, testa autenticação/Host/Origin/tamanho de corpo, assinatura/issuer/audience/expiração/scopes OAuth com chaves locais e rejeição de execução arbitrária. O teste de integração HTTP cria uma base 40 × 30 × 6 mm com furo Ø6, valida volume/sólido, salva FCStd/STEP/STL/PNG e reabre FCStd pelo MCP. A evidência é gravada em `http-integration-result.json` sem credenciais.

Esses testes não equivalem a uma chamada vinda do ChatGPT Web. Permanecem dependentes do ambiente/conta: instalar e executar o agente de túnel, RBAC de Tunnels e do workspace, configuração de um emissor OAuth real e seu fluxo interativo, encaminhamento Host/Origin pelo túnel e a chamada final no ChatGPT. Nenhum servidor foi publicado na internet.
