@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0web\stop-local.ps1"
if errorlevel 1 pause
