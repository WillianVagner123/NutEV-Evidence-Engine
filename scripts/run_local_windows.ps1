$ErrorActionPreference = "Stop"

Write-Host "NutEV/NutMEV local setup - Windows PowerShell"

if (-not (Test-Path ".venv")) {
    py -3.12 -m venv .venv
}

. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dashboard,platform]"
nutev demo-data --project-root ./project_output_demo

Write-Host ""
Write-Host "Setup concluido. Para abrir o dashboard:"
Write-Host "  . .\.venv\Scripts\Activate.ps1"
Write-Host "  nutev dashboard --project-root ./project_output_demo --port 8501"
Write-Host ""
Write-Host "Depois acesse: http://127.0.0.1:8501"
