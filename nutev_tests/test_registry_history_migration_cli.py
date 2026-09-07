from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "migrate_registry_history.py"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_refuses_any_run_without_explicit_dry_run(tmp_path: Path) -> None:
    report = tmp_path / "REGISTRY_MIGRATION_REPORT.json"

    result = run_cli("--source-root", str(tmp_path), "--report", str(report))

    assert result.returncode == 2
    assert "supports --dry-run only" in result.stderr
    assert "Apply/cutover requires a reviewed REGISTRY_MIGRATION_REPORT.json" in result.stderr
    assert not report.exists()


def test_cli_missing_source_writes_explicit_not_materialized_report(tmp_path: Path) -> None:
    missing = tmp_path / "project_output_missing"
    report = tmp_path / "REGISTRY_MIGRATION_REPORT.json"

    result = run_cli(
        "--dry-run",
        "--source-root",
        str(missing),
        "--report",
        str(report),
    )

    assert result.returncode == 3
    assert report.is_file()
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["status"] == "SOURCE_NOT_MATERIALIZED"
    assert payload["records_seen"] == 0
    assert payload["guardrails"]["target_registry_mutated"] is False
    assert payload["guardrails"]["legacy_files_deleted"] is False
    assert payload["guardrails"]["temporary_core_projection_only"] is True
    assert payload["guardrails"]["temporary_workbench_projection_only"] is True
