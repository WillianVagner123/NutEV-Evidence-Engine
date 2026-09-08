from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
DEATH_TEST = ROOT / "tools" / "multitenant_death_test.py"


def test_full_multitenant_death_matrix_runs_hermetically() -> None:
    completed = subprocess.run(
        [sys.executable, str(DEATH_TEST)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["record_type"] == "NUTEV_FULL_MULTITENANT_DEATH_TEST"
    assert report["schema_version"] == 1
    assert report["status"] == "PASS"
    assert report["tenant_count"] == 2
    assert report["project_count"] == 2
    assert report["checks_passed"] >= 14
    assert all(item["status"] == "PASS" for item in report["checks"])
    assert report["assertions"] == {
        "article1_state_modified": False,
        "article2_legacy_binding_modified": False,
        "historical_ownership_modified": False,
        "no_network_required": True,
        "platform_admin_private_bypass": False,
        "scientific_search_executed": False,
        "temporary_fixture_only": True,
    }


def test_death_test_has_no_production_or_remote_execution_path() -> None:
    source = DEATH_TEST.read_text(encoding="utf-8").casefold()
    assert "project_output_reference" not in source
    assert "hetzner" not in source
    assert "ssh" not in source
    assert "91.98." not in source
    assert "nutev_public_url" not in source
    assert "requests." not in source
    assert "urllib" not in source
    assert "http://" not in source
    assert "https://" not in source
    assert "tempfile.temporarydirectory" in source


def test_death_test_covers_every_pr12_private_boundary() -> None:
    source = DEATH_TEST.read_text(encoding="utf-8")
    required = (
        "context_cross_workspace_denied",
        "search_idor_denied",
        "search_job_idor_denied",
        "unowned_search_not_adopted",
        "placement_idor_denied",
        "full_text_grant_isolation",
        "application_idor_denied",
        "review_round_idor_denied",
        "review_assignment_idor_denied",
        "review_submit_lock_immutable",
        "export_idor_denied",
        "project_audit_chains_independent",
        "platform_admin_search_bypass_denied",
        "platform_admin_library_bypass_denied",
        "platform_admin_application_bypass_denied",
        "platform_admin_export_bypass_denied",
    )
    for marker in required:
        assert marker in source
