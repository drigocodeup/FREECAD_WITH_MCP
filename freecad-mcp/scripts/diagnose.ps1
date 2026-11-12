$Project = Split-Path $PSScriptRoot -Parent
Get-Command python,codex -ErrorAction SilentlyContinue | Select-Object Name,Source
& codex --version
$Settings = Get-Content "$Project\config\settings.json" -Raw | ConvertFrom-Json
Get-Item $Settings.freecad_executable | Select-Object FullName,VersionInfo
Push-Location $Project
try { & '.\.venv\Scripts\python.exe' -c "from bridge.client import call; print(call('health_check'))" }
finally { Pop-Location }
