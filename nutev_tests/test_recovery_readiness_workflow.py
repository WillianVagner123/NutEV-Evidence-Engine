from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CI = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
DEPLOY = (ROOT / ".github/workflows/deploy-hetzner.yml").read_text(encoding="utf-8")


def _job_block() -> str:
    marker = "  production-recovery-readiness:\n"
    assert marker in CI
    return CI.split(marker, 1)[1]


def test_recovery_readiness_is_main_push_only() -> None:
    block = _job_block()
    assert "github.event_name == 'push'" in block
    assert "github.ref == 'refs/heads/main'" in block
    assert "environment: HETZNER" in block


def test_recovery_readiness_never_stops_production_or_removes_volume() -> None:
    block = _job_block()
    assert "docker stop" not in block
    assert "docker volume rm" not in block
    assert "docker rm -f" not in block
    assert "production_running=true" in block
    assert "scientific_data_modified=false" in block


def test_failed_deploy_allowlist_controls_cleanup() -> None:
    block = _job_block()
    assert "deploy-hetzner.yml/runs?status=failure" in block
    assert "--allow-sha" in block
    assert "sha != current" in block
    assert "release_recovery_hygiene.py" in block


def test_capacity_is_checked_before_ci_can_trigger_deploy() -> None:
    block = _job_block()
    assert 'docker exec "$OLD_CONTAINER" du -sk /app/project_output_reference | cut -f1' in block
    assert "sh -c 'du -sk /app/project_output_reference" not in block
    assert "FREE_KB" in block
    assert "REQUIRED_KB" in block
    assert "snapshot_capacity=PASS" in block
    assert 'workflows: ["ci"]' in DEPLOY
