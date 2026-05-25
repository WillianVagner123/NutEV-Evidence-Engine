#!/usr/bin/env bash
set -euo pipefail

if [ ! -x ".venv/bin/nutev" ]; then
  echo "Ambiente nao encontrado. Rode primeiro: ./scripts/setup_unix.sh" >&2
  exit 1
fi

.venv/bin/nutev dashboard --project-root ./project_output_demo --port 8501
