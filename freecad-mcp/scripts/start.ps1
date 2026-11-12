param([switch]$PrepareOnly)
$ErrorActionPreference = 'Stop'
$Project = Split-Path $PSScriptRoot -Parent
$Python = Join-Path $Project '.venv\Scripts\python.exe'
$Runtime = Join-Path $Project '.runtime'
New-Item -ItemType Directory -Force $Runtime | Out-Null
# Restrict bridge credentials to this Windows user and SYSTEM.
$Identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$ProjectOwner = (Get-Acl $Project).Owner
& icacls.exe $Runtime /inheritance:r /grant:r "${Identity}:(OI)(CI)F" "${ProjectOwner}:(OI)(CI)F" 'SYSTEM:(OI)(CI)F' | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Nao foi possivel proteger .runtime' }
$Settings = Get-Content (Join-Path $Project 'config\settings.json') -Raw | ConvertFrom-Json
$Macro = Join-Path $Runtime 'StartBridge.FCMacro'
$ProjectLiteral = ConvertTo-Json ($Project -replace '\\','/') -Compress
$Code = @"
import sys, traceback
sys.path.insert(0, $ProjectLiteral)
try:
    from bridge.freecad_bridge import start
    start($ProjectLiteral)
    from cess_gui.toolbar import install
    install()
except Exception:
    from pathlib import Path
    Path($ProjectLiteral + '/.runtime/startup-error.log').write_text(traceback.format_exc(), encoding='utf-8')
    raise
"@
[IO.File]::WriteAllText($Macro, $Code, [Text.UTF8Encoding]::new($false))
if ($PrepareOnly) { Write-Output "Macro: $Macro"; return }
if (Test-Path (Join-Path $Runtime 'endpoint.json')) {
    Push-Location $Project
    try { & $Python -c "from bridge.client import call; print(call('health_check'))" }
    finally { Pop-Location }
    if ($LASTEXITCODE -eq 0) { return }
}
if (Get-Process freecad -ErrorAction SilentlyContinue) {
    throw "FreeCAD ja esta aberto. Execute a macro $Macro pelo menu Macro > Macros; o script preservou a instancia existente."
}
Start-Process -FilePath $Settings.freecad_executable -ArgumentList ('"' + $Macro + '"') -WindowStyle Hidden
Write-Output "FreeCAD iniciado. Bridge: $Macro"
