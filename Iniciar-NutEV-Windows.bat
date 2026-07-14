@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ============================================
echo    NutEV/NutMEV - iniciar painel (dashboard)
echo ============================================
echo.

REM --- 1) Encontrar Python 3.12+ ---
set "PY="
py -3.12 --version >nul 2>&1 && set "PY=py -3.12"
if not defined PY ( python --version >nul 2>&1 && set "PY=python" )
if not defined PY (
  echo [ERRO] Python 3.12+ nao encontrado.
  echo Instale em https://www.python.org/downloads/ e marque "Add Python to PATH".
  echo.
  pause
  exit /b 1
)

REM --- 2) Criar ambiente e instalar na primeira vez ---
if not exist ".venv\Scripts\nutev.exe" (
  echo ==^> Preparando o ambiente na primeira vez. Isso pode levar alguns minutos...
  %PY% -m venv .venv
  ".venv\Scripts\python.exe" -m pip install --upgrade pip
  REM dashboard = painel; documents = leitura de PDF/OCR; search = coleta real.
  ".venv\Scripts\python.exe" -m pip install -e ".[dashboard,documents,search]"
  if errorlevel 1 (
    echo [ERRO] Falha na instalacao. Veja as mensagens acima.
    pause
    exit /b 1
  )
)

REM --- 3) Gerar dados de demonstracao se ainda nao existirem ---
if not exist "project_output_demo\07_logs\run_summary.json" (
  echo ==^> Gerando dados de demonstracao...
  ".venv\Scripts\nutev.exe" demo-data --project-root ".\project_output_demo"
)

REM --- 4) Abrir o painel no navegador ---
echo.
echo ==^> Abrindo o painel em http://localhost:8501
echo     (para PARAR, feche esta janela)
echo.
".venv\Scripts\nutev.exe" dashboard --project-root ".\project_output_demo"

pause
