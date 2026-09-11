"""Static workflow linkage checks; execution proof remains in GitHub Actions."""
from pathlib import Path
import importlib.util
import json
import os
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("release_gate_contract", ROOT / "tools/check_release_prerequisites.py")
assert SPEC and SPEC.loader
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


def text(name):
    return (ROOT / ".github/workflows" / name).read_text(encoding="utf-8")


def test_production_job_depends_on_gate_and_rechecks_before_ssh():
    source = text("deploy-hetzner.yml")
    before, deploy = source.split("\n  deploy:\n", 1)
    assert "release-prerequisites:" in before
    assert "environment: HETZNER" not in before
    assert "secrets.HETZNER_SSH_KEY" not in before
    assert "head_repository.full_name == github.repository" in before
    assert "github.ref == 'refs/heads/main'" in before
    assert "needs: release-prerequisites" in deploy
    assert "needs.release-prerequisites.result == 'success'" in deploy
    assert "TARGET_SHA: ${{ needs.release-prerequisites.outputs.target_sha }}" in deploy
    assert deploy.index("Revalidate candidate") < deploy.index("Validate deployment configuration")
    assert deploy.index("tools/check_release_prerequisites.py") < deploy.index("- name: Configure SSH")
    assert "HETZNER_SSH_KEY" not in deploy.split("    steps:", 1)[0]
    assert source.count("secrets.HETZNER_SSH_KEY") == 2
    assert "actions: read" in source


@pytest.mark.parametrize("path,step", [
    (path, step) for path, jobs in GATE.REQUIRED.items() for steps in jobs.values() for step in steps
])
def test_gate_required_step_names_match_versioned_workflows(path, step):
    assert f"- name: {step}\n" in (ROOT / path).read_text(encoding="utf-8")


def test_dependency_and_artifact_checks_run_on_main_sha():
    for name in ("dependency-review.yml", "release-artifact-validation.yml"):
        assert 'push:\n    branches: ["main"]' in text(name)
    source = text("dependency-review.yml")
    assert "base-ref: ${{ steps.refs.outputs.base }}" in source
    assert "head-ref: ${{ steps.refs.outputs.head }}" in source
    assert "warn-only: true" not in source
    assert "continue-on-error: true" not in source


def test_tenant_audit_is_hermetic_and_retains_sha_evidence():
    source = text("multitenant-release-audit.yml")
    assert "environment: HETZNER" not in source
    assert "secrets.HETZNER" not in source
    assert 'NUTEV_DISABLE_NETWORK: "1"' in source
    assert 'git archive --format=tar.gz' in source
    assert 'tools/multitenant_death_test.py --output closeout_artifacts/multitenant-death.json' in source
    assert 'source_archive_sha256' in source
    assert 'temporary_fixture_only' in source


@pytest.mark.parametrize("kind,base,head,allowed", [
    ("push", "a" * 40, "b" * 40, True),
    ("pull_request", "a" * 40, "b" * 40, True),
    ("push", "0" * 40, "b" * 40, False),
    ("push", "b" * 40, "b" * 40, False),
    ("push", "main", "b" * 40, False),
    ("release", "a" * 40, "b" * 40, False),
])
def test_dependency_ref_resolver_uses_real_immutable_refs(tmp_path, kind, base, head, allowed):
    source = text("dependency-review.yml")
    body = source.split("python3 - <<'PYREF'\n", 1)[1].split("          PYREF", 1)[0]
    body = "\n".join(line[10:] for line in body.splitlines())
    event = {"before": base, "pull_request": {"base": {"sha": base}, "head": {"sha": head}}}
    payload, output = tmp_path / "event.json", tmp_path / "output.txt"
    payload.write_text(json.dumps(event), encoding="utf-8")
    env = dict(os.environ, GITHUB_EVENT_PATH=str(payload), GITHUB_OUTPUT=str(output),
               GITHUB_EVENT_NAME=kind, GITHUB_SHA=head)
    result = subprocess.run([sys.executable, "-c", body], env=env, capture_output=True, text=True)
    assert (result.returncode == 0) is allowed, result.stderr
    if allowed:
        assert output.read_text() == f"base={base}\nhead={head}\n"
    else:
        assert not output.exists()
