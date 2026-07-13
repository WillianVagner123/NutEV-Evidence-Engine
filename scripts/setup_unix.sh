#!/usr/bin/env bash
set -euo pipefail

step() {
  printf '\n==> %s\n' "$1"
}

if [ ! -f "pyproject.toml" ]; then
  echo "Execute este script dentro da pasta raiz do repositorio NutEV-Evidence-Engine." >&2
  exit 1
fi

resolve_python() {
  for cmd in python3.12 python3.13 python3 python; do
    if command -v "$cmd" >/dev/null 2>&1; then
      if "$cmd" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 12) and sys.version_info < (3, 15) else 1)
PY
      then
        echo "$cmd"
        return 0
      fi
    fi
  done
  return 1
}

step "Validando Python"
PYTHON_CMD="$(resolve_python || true)"
if [ -z "$PYTHON_CMD" ]; then
  echo "Instale Python 3.12 ou 3.13 e tente novamente." >&2
  exit 1
fi
echo "Python selecionado: $PYTHON_CMD"

step "Criando ambiente virtual .venv"
if [ ! -d ".venv" ]; then
  "$PYTHON_CMD" -m venv .venv
fi

VENV_PYTHON=".venv/bin/python"
VENV_NUTEV=".venv/bin/nutev"

step "Atualizando pip"
"$VENV_PYTHON" -m pip install --upgrade pip

step "Instalando NutEV/NutMEV com dashboard e API"
"$VENV_PYTHON" -m pip install -e ".[dashboard,platform]"

step "Instalando navegador Chromium do Playwright quando disponivel"
if ! "$VENV_PYTHON" -m playwright install chromium; then
  echo "Aviso: Playwright Chromium nao foi instalado automaticamente. Para captura web, rode depois: .venv/bin/python -m playwright install chromium" >&2
fi

step "Gerando dados demo"
"$VENV_NUTEV" demo-data --project-root ./project_output_demo

step "Checando instalacao"
"$VENV_PYTHON" scripts/check_local.py

echo ""
echo "Pronto. Para abrir o dashboard:"
echo "  ./scripts/run_dashboard_unix.sh"
echo ""
echo "Para abrir a API local:"
echo "  ./scripts/run_api_unix.sh"
