#!/usr/bin/env bash
set -euo pipefail

# One command to open the NutEV site locally. Then click "▶ Rodar pipeline".
echo "NutEV/NutMEV — site local"

if [ ! -d ".venv" ]; then
  python3.12 -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[platform]"
mkdir -p ./project_output

echo ""
echo "Abrindo http://127.0.0.1:8000  — clique em '▶ Rodar pipeline'."
echo "(Ctrl+C para parar o servidor.)"
nutev serve --project-root ./project_output --host 127.0.0.1 --port 8000
