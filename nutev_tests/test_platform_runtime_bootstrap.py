from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import subprocess
import sys

from nutev.tenancy import CORE_PLATFORM_TABLES, initialize_platform_database


ROOT = Path(__file__).resolve().parents[1]


def _row_count(database: Path, table: str) -> int:
    with sqlite3.connect(database) as connection:
        row = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
    assert row is not None
    return int(row[0])


def test_platform_bootstrap_is_idempotent_and_creates_no_owned_or_scientific_state(
    tmp_path: Path,
) -> None:
    database = tmp_path / "project_output_reference" / "platform" / "auth.sqlite3"

    first = initialize_platform_database(database)
    second = initialize_platform_database(database)

    assert first == second == tuple(sorted(CORE_PLATFORM_TABLES))
    assert database.is_file()
    for table in (
        "platform_auth_users",
        "platform_workspaces",
        "platform_projects",
        "platform_research_applications",
    ):
        assert _row_count(database, table) == 0


def test_empty_bootstrapped_platform_is_readable_by_production_doctorate_audit(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "project_output_reference"
    database = output_root / "platform" / "auth.sqlite3"
    initialize_platform_database(database)

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "audit_doctorate_runtime.py"),
            "--database",
            str(database),
            "--output-root",
            str(output_root),
            "--json",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["status"] == "PASS"
    assert report["read_only"] is True
    assert report["scientific_state_modified"] is False
    assert report["legacy_binding_performed"] is False
    assert report["search_executed"] is False
    assert report["article1"]["application_count"] == 0
    assert report["article2"]["application_count"] == 0


def test_production_image_bootstraps_schema_only_in_pilot_mode() -> None:
    dockerfile = (ROOT / "deploy" / "hetzner" / "Dockerfile").read_text(encoding="utf-8")
    assert "NUTEV_AUTH_MODE:-legacy" in dockerfile
    assert "= pilot ]; then python tools/bootstrap_platform_runtime.py; fi" in dockerfile
    assert dockerfile.index("bootstrap_platform_runtime.py") < dockerfile.index("secure_server.py --host")
