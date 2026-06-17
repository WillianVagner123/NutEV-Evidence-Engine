$ErrorActionPreference = "Stop"

# One command to open the NutEV site locally. Then click "▶ Rodar pipeline".
Write-Host "NutEV/NutMEV - site local"

if (-not (Test-Path ".venv")) {
    py -3.12 -m venv .venv
}

. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[platform]"
New-Item -ItemType Directory -Force -Path ".\project_output" | Out-Null

Write-Host ""
Write-Host "Abrindo http://127.0.0.1:8000  - clique em '> Rodar pipeline'."
Write-Host "(Ctrl+C para parar o servidor.)"
nutev serve --project-root ./project_output --host 127.0.0.1 --port 8000
