"""Safety contract for the operator-triggered membership workflow.

The workflow reaches production over SSH, so its guarantees are asserted here
rather than trusted to review: it must handle no credential, must not be able to
assign workspace ownership or a global role, and must refuse a grant before
touching anything when the target account or workspace is not in the expected
state.

The preflight guard embedded in the workflow is extracted and executed against
fixtures, so a change that weakens it fails the suite instead of being
discovered during a production run.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "provision-supervisor-access.yml"


@pytest.fixture(scope="module")
def workflow() -> dict:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def steps(workflow: dict) -> list[dict]:
    return workflow["jobs"]["membership"]["steps"]


def _step(steps: list[dict], prefix: str) -> dict:
    for step in steps:
        if str(step.get("name") or "").startswith(prefix):
            return step
    raise AssertionError(f"workflow step starting with {prefix!r} not found")


def test_workflow_is_manual_only_and_gated_by_the_hetzner_environment(workflow: dict) -> None:
    triggers = workflow[True] if True in workflow else workflow["on"]
    assert set(triggers) == {"workflow_dispatch"}, "must not run automatically"

    job = workflow["jobs"]["membership"]
    assert job["environment"] == "HETZNER", "must inherit the environment approval gate"
    assert workflow["permissions"] == {"contents": "read"}, "must not hold write scopes"
    assert workflow["concurrency"]["cancel-in-progress"] is False


def test_workflow_cannot_assign_ownership_or_a_global_role(workflow: dict) -> None:
    triggers = workflow[True] if True in workflow else workflow["on"]
    roles = triggers["workflow_dispatch"]["inputs"]["role"]["options"]

    assert "WORKSPACE_OWNER" not in roles
    assert "WORKSPACE_ADMIN" not in roles
    assert "PLATFORM_ADMIN" not in roles
    assert roles[0] == "ACADEMIC_SUPERVISOR", "the supervision role is the default"


def test_workflow_handles_no_credential(workflow: dict) -> None:
    """No account creation, password or invitation means no secret to leak."""

    body = WORKFLOW.read_text(encoding="utf-8")
    # Credential-handling constructs, not the mere word: the guard's error message
    # legitimately points the operator at /set-password.html, and a test that banned
    # the substring would punish helpful text while catching nothing real.
    forbidden = (
        "provision_nutev_user",
        "seed_bootstrap_access_invitation",
        "grant_platform_admin",
        "accept_invitation",
        "provision_user(",
        "--platform-admin",
        "getpass",
        "secrets.token",
        "password_hash",
    )
    script = "\n".join(
        str(step.get("run") or "") for step in workflow["jobs"]["membership"]["steps"]
    )
    for token in forbidden:
        assert token not in script, f"workflow script must not reference {token!r}"

    # The only tool it may invoke is the membership grant.
    invoked = {line.strip() for line in script.splitlines() if "tools/" in line}
    assert all("grant_workspace_membership.py" in line for line in invoked), invoked

    # The only secret it may read is the deployment SSH key.
    assert body.count("secrets.") == 1
    assert "secrets.HETZNER_SSH_KEY" in body


def test_grant_step_runs_only_in_grant_mode(steps: list[dict]) -> None:
    grant = _step(steps, "Grant workspace membership")
    assert grant["if"].strip() == "${{ inputs.mode == 'grant' }}"

    script = grant["run"]
    assert "tools/grant_workspace_membership.py" in script
    assert "--role \"$ROLE\"" in script


def test_inspect_runs_before_grant(steps: list[dict]) -> None:
    names = [str(step.get("name") or "") for step in steps]
    inspect_at = next(i for i, n in enumerate(names) if n.startswith("Inspect"))
    grant_at = next(i for i, n in enumerate(names) if n.startswith("Grant"))
    assert inspect_at < grant_at, "state must be verified before any mutation"


def _guard_source(steps: list[dict]) -> str:
    script = _step(steps, "Inspect")["run"]
    return script.split("python3 - <<'PY'\n", 1)[1].split("\nPY\n", 1)[0]


def _run_guard(
    source: str,
    payload,
    workspace: str,
    tmp_path: Path,
    *,
    mode: str = "grant",
):
    body = payload if isinstance(payload, str) else json.dumps(payload)
    (tmp_path / "inspect.json").write_text(body, encoding="utf-8")
    guard = tmp_path / "guard.py"
    guard.write_text(source, encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(guard)],
        cwd=tmp_path,
        env={"PATH": "/usr/bin:/bin", "TARGET_WORKSPACE": workspace, "MODE": mode},
        capture_output=True,
        text=True,
    )


def test_an_unreadable_reply_is_never_read_as_an_empty_platform(
    steps: list[dict],
    tmp_path: Path,
) -> None:
    """The failure that matters: garbage must not look like "no workspaces exist"."""

    source = _guard_source(steps)

    for body in ("", "   ", "curl: (7) Failed to connect", "<html>502</html>"):
        result = _run_guard(source, body, "lab", tmp_path, mode="inspect")
        assert result.returncode == 7, f"{body!r} was accepted: {result.stdout}"
        assert "not an empty result" in result.stderr

    # A well-formed reply that simply lacks the list is refused just the same.
    result = _run_guard(source, {"account": None}, "lab", tmp_path, mode="inspect")
    assert result.returncode == 7
    assert "no 'workspaces' list" in result.stderr


def test_inspect_reports_state_to_the_log_without_applying_grant_rules(
    steps: list[dict],
    tmp_path: Path,
) -> None:
    """inspect is read-only: it must report, not refuse, when an account is absent."""

    payload = {
        "workspaces": [
            {"slug": "nutev-doutorado", "name": "NutEV Doutorado", "status": "active"}
        ],
        "account": None,
        "memberships": [],
    }
    result = _run_guard(_guard_source(steps), payload, "", tmp_path, mode="inspect")

    assert result.returncode == 0, result.stderr
    # The operator reads the log, so the slug has to be there and not only in the summary.
    assert "nutev-doutorado" in result.stdout
    assert "WORKSPACES:" in result.stdout


def test_inspect_says_plainly_when_no_workspace_exists(
    steps: list[dict],
    tmp_path: Path,
) -> None:
    payload = {"workspaces": [], "account": None, "memberships": []}
    result = _run_guard(_guard_source(steps), payload, "", tmp_path, mode="inspect")

    assert result.returncode == 0, result.stderr
    assert "(none)" in result.stdout
    assert "must exist before a membership can be granted" in result.stdout


@pytest.mark.parametrize(
    ("payload", "workspace", "code", "needle"),
    [
        (
            {"workspaces": [{"slug": "lab", "name": "Lab", "status": "active"}], "account": None},
            "lab",
            4,
            "No account exists",
        ),
        (
            {"workspaces": [{"slug": "lab", "name": "Lab", "status": "active"}], "account": {"email": "a@b.c", "display_name": "A", "status": "disabled"}},
            "lab",
            5,
            "not active",
        ),
        (
            {"workspaces": [{"slug": "lab", "name": "Lab", "status": "active"}], "account": {"email": "a@b.c", "display_name": "A", "status": "active"}},
            "ausente",
            6,
            "not found",
        ),
        (
            {"workspaces": [{"slug": "lab", "name": "Lab", "status": "active"}], "account": {"email": "a@b.c", "display_name": "A", "status": "active"}},
            "lab",
            0,
            "",
        ),
    ],
    ids=["no_account", "inactive_account", "unknown_workspace", "ready"],
)
def test_preflight_guard_refuses_before_mutating(
    steps: list[dict],
    tmp_path: Path,
    payload: dict,
    workspace: str,
    code: int,
    needle: str,
) -> None:
    result = _run_guard(_guard_source(steps), payload, workspace, tmp_path)
    assert result.returncode == code, result.stderr
    if needle:
        assert needle in result.stderr
