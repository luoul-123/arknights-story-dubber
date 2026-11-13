@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0web\setup-local.ps1"
if errorlevel 1 pause
