$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv\Scripts\nutev.exe")) {
    throw "Ambiente nao encontrado. Rode primeiro: .\scripts\setup_windows.ps1"
}

$env:PYTHONPATH = Join-Path (Resolve-Path ".").Path "src"

& .\.venv\Scripts\nutev.exe dashboard --project-root ./project_output_demo --port 8501
