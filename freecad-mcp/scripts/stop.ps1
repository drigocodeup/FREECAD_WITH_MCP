$Project = Split-Path $PSScriptRoot -Parent
Push-Location $Project
try { & '.\.venv\Scripts\python.exe' -c "from bridge.client import call; print(call('shutdown_bridge'))" }
finally { Pop-Location }
