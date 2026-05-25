"""Verificador simples da instalacao local NutEV/NutMEV."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def ok(message: str) -> None:
    print(f"[OK] {message}")


def warn(message: str) -> None:
    print(f"[AVISO] {message}")


def fail(message: str) -> None:
    print(f"[ERRO] {message}")
    raise SystemExit(1)


def check_python() -> None:
    version = sys.version_info
    if not ((3, 12) <= (version.major, version.minor) < (3, 15)):
        fail(f"Python incompatível: {sys.version}. Use Python 3.12 ou 3.13.")
    ok(f"Python {version.major}.{version.minor}.{version.micro}")


def check_root() -> None:
    if not (ROOT / "pyproject.toml").exists():
        fail("pyproject.toml nao encontrado. Rode a partir da raiz do repositorio.")
    ok("Raiz do repositorio encontrada")


def check_module(module_name: str, label: str | None = None) -> None:
    label = label or module_name
    if importlib.util.find_spec(module_name) is None:
        fail(f"Modulo ausente: {label}. Rode pip install -e \".[dashboard,platform]\".")
    ok(f"Modulo disponivel: {label}")


def check_command() -> None:
    nutev = shutil.which("nutev")
    if nutev:
        ok(f"Comando nutev encontrado: {nutev}")
        return

    candidate = ROOT / ".venv" / ("Scripts" if sys.platform.startswith("win") else "bin") / ("nutev.exe" if sys.platform.startswith("win") else "nutev")
    if candidate.exists():
        ok(f"Comando nutev encontrado no ambiente virtual: {candidate}")
        return

    fail("Comando nutev nao encontrado. Reinstale com pip install -e \".[dashboard,platform]\".")


def check_demo_output() -> None:
    demo = ROOT / "project_output_demo"
    if demo.exists():
        ok("Pasta project_output_demo existe")
    else:
        warn("project_output_demo ainda nao existe. Gere com: nutev demo-data --project-root ./project_output_demo")


def check_cli_version_smoke() -> None:
    nutev = shutil.which("nutev")
    if not nutev:
        candidate = ROOT / ".venv" / ("Scripts" if sys.platform.startswith("win") else "bin") / ("nutev.exe" if sys.platform.startswith("win") else "nutev")
        nutev = str(candidate) if candidate.exists() else None
    if not nutev:
        return
    try:
        subprocess.run([nutev, "--help"], cwd=ROOT, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
        ok("CLI nutev responde ao --help")
    except Exception as exc:  # noqa: BLE001
        warn(f"CLI nutev encontrada, mas --help falhou: {exc}")


def main() -> None:
    print("Checando ambiente local NutEV/NutMEV...\n")
    check_python()
    check_root()
    check_module("nutev", "nutev")
    check_module("streamlit", "streamlit/dashboard")
    check_module("fastapi", "fastapi/API")
    check_command()
    check_demo_output()
    check_cli_version_smoke()
    print("\nAmbiente local verificado.")


if __name__ == "__main__":
    main()
