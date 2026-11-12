$ErrorActionPreference = 'Stop'
$Project = Split-Path $PSScriptRoot -Parent
$Python = Join-Path $Project '.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $Python)) { throw 'Execute scripts/install.ps1 antes de iniciar o MCP.' }
& $Python (Join-Path $Project 'server_http.py')
exit $LASTEXITCODE
