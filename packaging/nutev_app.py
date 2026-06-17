"""Entry point for the packaged NutEV desktop app (PyInstaller).

Double-clicking the .exe (no args) opens the local site in the browser. Any args
are forwarded to the normal CLI, so the in-app "▶ Play" button can re-invoke the
same .exe to run the pipeline (see src/nutev/api/routes.py).
"""
from __future__ import annotations

import multiprocessing
import os
import sys
from pathlib import Path


def _default_project_root() -> Path:
    base = Path(os.environ.get("NUTEV_HOME") or (Path.home() / "NutEV"))
    base.mkdir(parents=True, exist_ok=True)
    return base


def run() -> None:
    from nutev.cli import main

    if len(sys.argv) <= 1:  # double-clicked -> open the site
        root = str(_default_project_root())
        sys.argv = [sys.argv[0], "serve", "--project-root", root, "--host", "127.0.0.1", "--port", "8000"]
    main()


if __name__ == "__main__":
    multiprocessing.freeze_support()  # safe no-op if multiprocessing is unused
    run()
