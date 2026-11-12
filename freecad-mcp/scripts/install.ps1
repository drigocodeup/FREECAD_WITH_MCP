$ErrorActionPreference = 'Stop'
$Project = Split-Path $PSScriptRoot -Parent
if (!(Test-Path "$Project\.venv\Scripts\python.exe")) { python -m venv "$Project\.venv" }
& "$Project\.venv\Scripts\python.exe" -m pip install -r "$Project\requirements.txt"
if ($LASTEXITCODE -ne 0) { throw 'Instalacao falhou' }
Write-Output "Python: $Project\.venv\Scripts\python.exe"
Write-Output "Servidor: $Project\server.py"
