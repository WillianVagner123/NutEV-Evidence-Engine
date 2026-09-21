"""Safety contract for the workspace-provisioning workflow.

Unlike the membership workflow, this one writes state into an empty production
platform, so two things are asserted here rather than trusted to review: it must
handle no credential and grant no global role, and it must still surface the
tool's receipt when the tool refuses — the refusal message is the whole point of
a fail-closed tool, and losing it to errexit would leave an operator guessing.

The provisioning step is extracted from the workflow and executed against a
stubbed `ssh`, so these assertions cover the shipped text.
"""
from __future__ import annotations

import json
from pathlib import Path
import stat
import subprocess
import textwrap

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "provision-workspace.yml"
STEP_NAME = "Provision workspace and project"


@pytest.fixture(scope="module")
def workflow() -> dict:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def _step_script(workflow: dict, name: str) -> str:
    for step in workflow["jobs"]["workspace"]["steps"]:
        if str(step.get("name") or "") == name:
            return str(step["run"])
    raise AssertionError(f"step {name!r} not found")


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def _run_step(
    workflow: dict,
    tmp_path: Path,
    *,
    receipt: str,
    exit_code: int,
) -> subprocess.CompletedProcess:
    stubs = tmp_path / "stubs"
    stubs.mkdir(parents=True, exist_ok=True)
    _write_executable(
        stubs / "ssh",
        textwrap.dedent(
            f"""\
            #!/usr/bin/env bash
            cat > /dev/null
            printf '%s\\n' {json.dumps(receipt)}
            exit {exit_code}
            """
        ),
    )
    script = tmp_path / "step.sh"
    script.write_text(_step_script(workflow, STEP_NAME), encoding="utf-8")
    summary = tmp_path / "summary.md"
    summary.touch()
    return subprocess.run(
        ["bash", str(script)],
        cwd=tmp_path,
        env={
            "PATH": f"{stubs}:/usr/bin:/bin",
            "HETZNER_HOST": "host.invalid",
            "HETZNER_USER": "operator",
            "HETZNER_PORT": "22",
            "HETZNER_APP_DIR": "/srv/app",
            "OWNER_EMAIL": "owner@example.org",
            "WORKSPACE_NAME": "NutEV Doutorado",
            "WORKSPACE_SLUG": "nutev-doutorado",
            "PROJECT_NAME": "Artigo 1",
            "PROJECT_SLUG": "artigo-1",
            "PROJECT_TYPE": "generic",
            "GITHUB_STEP_SUMMARY": str(summary),
        },
        capture_output=True,
        text=True,
    )


def test_workflow_is_manual_only_and_gated_by_the_environment(workflow: dict) -> None:
    triggers = workflow[True] if True in workflow else workflow["on"]
    assert set(triggers) == {"workflow_dispatch"}
    assert workflow["jobs"]["workspace"]["environment"] == "HETZNER"
    assert workflow["permissions"] == {"contents": "read"}


def test_workflow_handles_no_credential_and_grants_no_global_role(workflow: dict) -> None:
    body = WORKFLOW.read_text(encoding="utf-8")
    script = "\n".join(
        str(step.get("run") or "") for step in workflow["jobs"]["workspace"]["steps"]
    )
    for token in (
        "provision_nutev_user",
        "grant_platform_admin",
        "seed_bootstrap_access_invitation",
        "accept_invitation",
        "--platform-admin",
        "getpass",
        "password_hash",
    ):
        assert token not in script, f"must not reference {token!r}"

    invoked = {line.strip() for line in script.splitlines() if "tools/" in line}
    assert all("provision_workspace_project.py" in line for line in invoked), invoked

    assert body.count("secrets.") == 1
    assert "secrets.HETZNER_SSH_KEY" in body


def test_a_refusal_still_reports_the_receipt_and_propagates_the_code(
    workflow: dict,
    tmp_path: Path,
) -> None:
    """The failure an operator will actually hit: no account for that address."""

    receipt = json.dumps(
        {
            "status": "owner_not_found",
            "changed": False,
            "accounts_on_platform": 0,
            "hint": "No account has been provisioned at all; complete the first-admin bootstrap.",
        }
    )
    result = _run_step(workflow, tmp_path, receipt=receipt, exit_code=4)

    assert result.returncode == 4, "the tool's exit code must reach the job"
    assert "owner_not_found" in result.stdout, "the receipt must survive the refusal"
    assert "accounts_on_platform: 0" in result.stdout
    assert "complete the first-admin bootstrap" in result.stdout
    assert (tmp_path / "summary.md").read_text(encoding="utf-8").strip() != ""


def test_a_successful_provision_reports_the_identifiers(
    workflow: dict,
    tmp_path: Path,
) -> None:
    receipt = json.dumps(
        {
            "status": "provisioned",
            "changed": True,
            "workspace": {
                "id": "wsp_" + "0" * 32,
                "name": "NutEV Doutorado",
                "slug": "nutev-doutorado",
                "created_now": True,
            },
            "project": {
                "id": "prj_" + "0" * 32,
                "name": "Artigo 1",
                "slug": "artigo-1",
                "created_now": True,
            },
        }
    )
    result = _run_step(workflow, tmp_path, receipt=receipt, exit_code=0)

    assert result.returncode == 0, result.stderr
    assert "nutev-doutorado" in result.stdout
    assert "artigo-1" in result.stdout
    assert "wsp_" in result.stdout, "the operator needs the workspace id"


def test_an_unreadable_receipt_is_never_reported_as_success(
    workflow: dict,
    tmp_path: Path,
) -> None:
    for body in ("", "Error response from daemon: container not running"):
        result = _run_step(workflow, tmp_path / body[:8].replace(" ", "_"), receipt=body, exit_code=0)
        assert result.returncode == 7, f"{body!r} was accepted"
        assert "readable receipt" in result.stderr
