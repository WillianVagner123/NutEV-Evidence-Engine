#!/usr/bin/env bash
set -eo pipefail  # not -u: venv activate scripts can reference unset vars

# Run from the repo root no matter where this is invoked from (scripts/ is one
# level down), so the relative .venv / project_output / pip install paths resolve.
cd "$(dirname "$0")/.." || exit 1

# Open the NutEV site locally, then click "▶ Rodar pipeline" in the browser.
# Idempotent: creates the venv + installs only on first run; fast afterwards.
echo "NutEV/NutMEV — site local"

# Find a usable Python (3.12–3.14).
PYBIN=""
for c in python3.12 python3.13 python3.14 python3 python; do
  if command -v "$c" >/dev/null 2>&1; then PYBIN="$c"; break; fi
done
if [ -z "$PYBIN" ]; then
  echo "Python 3.12+ não encontrado. Instale em https://www.python.org/downloads/" >&2
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "Criando ambiente .venv (primeira vez)…"
  "$PYBIN" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

# Install only if the CLI isn't there yet (first run / incomplete venv).
if ! command -v nutev >/dev/null 2>&1; then
  echo "Instalando dependências (primeira vez, pode demorar um pouco)…"
  python -m pip install --upgrade pip
  pip install -e ".[platform]"
fi

mkdir -p ./project_output

echo ""
echo "Abrindo http://127.0.0.1:8000  — clique em '▶ Rodar pipeline'."
echo "(Ctrl+C para parar o servidor.)"
nutev serve --project-root ./project_output --host 127.0.0.1 --port 8000
