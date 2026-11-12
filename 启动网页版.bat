@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0web\start-local.ps1"
if errorlevel 1 pause
