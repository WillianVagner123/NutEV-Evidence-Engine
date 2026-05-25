#!/usr/bin/env bash
set -euo pipefail

echo "NutEV/NutMEV local setup - macOS/Linux"

if [ ! -d ".venv" ]; then
  python3.12 -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dashboard,platform]"
nutev demo-data --project-root ./project_output_demo

echo ""
echo "Setup concluido. Para abrir o dashboard:"
echo "  source .venv/bin/activate"
echo "  nutev dashboard --project-root ./project_output_demo --port 8501"
echo ""
echo "Depois acesse: http://127.0.0.1:8501"
