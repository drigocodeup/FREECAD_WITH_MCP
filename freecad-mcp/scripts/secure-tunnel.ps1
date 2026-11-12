param(
    [ValidateSet('Help','Doctor','Run')][string]$Action = 'Help',
    [string]$Profile = 'freecad-local',
    [string]$ClientPath = $env:FREECAD_TUNNEL_CLIENT
)
$ErrorActionPreference = 'Stop'
if (!$ClientPath) {
    $Command = Get-Command tunnel-client -ErrorAction SilentlyContinue
    if ($Command) { $ClientPath = $Command.Source }
}
if (!$ClientPath -or !(Test-Path -LiteralPath $ClientPath)) {
    [Console]::Error.WriteLine('tunnel-client nao localizado. Consulte docs/TRANSPORTS.md e o download oficial em https://github.com/openai/tunnel-client/releases/latest. Nada foi instalado ou conectado.')
    exit 2
}
if ($Action -eq 'Help') { & $ClientPath help quickstart; exit $LASTEXITCODE }
if ($Action -eq 'Doctor') { & $ClientPath doctor --profile $Profile --explain; exit $LASTEXITCODE }
if (!$env:CONTROL_PLANE_API_KEY) { throw 'Defina CONTROL_PLANE_API_KEY no ambiente local; nunca coloque a chave em argumentos ou arquivos versionados.' }
& $ClientPath run --profile $Profile
exit $LASTEXITCODE
