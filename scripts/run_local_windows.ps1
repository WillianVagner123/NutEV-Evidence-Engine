$ErrorActionPreference = "Stop"

# Open the NutEV site locally, then click "▶ Rodar pipeline" in the browser.
# Idempotent: creates the venv + installs only on first run; fast afterwards.
Write-Host "NutEV/NutMEV - site local"

# Run from the repo root (this script lives in scripts/).
Set-Location (Split-Path $PSScriptRoot -Parent)

# Find a usable Python launcher.
$py = $null
if (Get-Command py -ErrorAction SilentlyContinue) { $py = "py -3.12" }
elseif (Get-Command python -ErrorAction SilentlyContinue) { $py = "python" }
if (-not $py) {
    Write-Host "Python 3.12+ nao encontrado. Instale em https://www.python.org/downloads/"
    Read-Host "Pressione Enter para sair"; exit 1
}

if (-not (Test-Path ".venv")) {
    Write-Host "Criando ambiente .venv (primeira vez)..."
    Invoke-Expression "$py -m venv .venv"
}
. .\.venv\Scripts\Activate.ps1

if (-not (Get-Command nutev -ErrorAction SilentlyContinue)) {
    Write-Host "Instalando dependencias (primeira vez, pode demorar)..."
    python -m pip install --upgrade pip
    pip install -e ".[platform]"
}

New-Item -ItemType Directory -Force -Path ".\project_output" | Out-Null

Write-Host ""
Write-Host "Abrindo http://127.0.0.1:8000  - clique em '> Rodar pipeline'."
Write-Host "(Ctrl+C para parar o servidor.)"
nutev serve --project-root ./project_output --host 127.0.0.1 --port 8000
