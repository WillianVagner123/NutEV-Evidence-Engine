#!/bin/bash
# Double-click this file (macOS) to open the NutEV site locally.
# Linux: run "bash start-nutev.command" from a terminal.
cd "$(dirname "$0")" || exit 1
exec bash scripts/run_local_unix.sh
