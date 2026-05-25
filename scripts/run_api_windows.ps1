$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv\Scripts\nutev.exe")) {
    throw "Ambiente nao encontrado. Rode primeiro: .\scripts\setup_windows.ps1"
}

& .\.venv\Scripts\nutev.exe serve --project-root ./project_output_demo --host 127.0.0.1 --port 8000
