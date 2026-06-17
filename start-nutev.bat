@echo off
REM Double-click this file (Windows) to open the NutEV site locally.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\run_local_windows.ps1"
echo.
echo (Servidor encerrado.)
pause
