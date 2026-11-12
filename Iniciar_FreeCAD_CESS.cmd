@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0freecad-mcp\scripts\start.ps1"
if errorlevel 1 pause
