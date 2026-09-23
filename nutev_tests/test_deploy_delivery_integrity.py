"""The production deploy must not be able to report success while half-executed.

The remote half of the Hetzner deploy used to be streamed into ``bash -s`` over the SSH
channel. When that channel was disturbed around the container restart, bash reached EOF
mid-script and exited 0, so ``ssh`` returned success and the job went green having skipped
the post-promotion runtime contract, the build-identity assertion, the public HTTPS edge
smoke and the rollback safety net. A real deploy did exactly that: its log contains no
output from any of those checks, only the echoed script text.

These tests pin the two properties that make that failure impossible to repeat quietly:
delivery is verified before execution, and completion is asserted after it.
"""
from __future__ import annotations

import re
import subprocess

import yaml

from deploy_surface import DEPLOY_WORKFLOW, REMOTE_DEPLOY_SCRIPT

WORKFLOW = DEPLOY_WORKFLOW.read_text(encoding="utf-8")
SCRIPT = REMOTE_DEPLOY_SCRIPT.read_text(encoding="utf-8")
SENTINEL = "NUTEV_REMOTE_DEPLOY_COMPLETE"


def _deploy_steps() -> list[dict]:
    return yaml.safe_load(WORKFLOW)["jobs"]["deploy"]["steps"]


def _step(name: str) -> dict:
    return next(step for step in _deploy_steps() if step.get("name") == name)


def test_remote_script_is_a_real_file_and_parses() -> None:
    """Guard the guard: if the script vanished, the surface tests would be vacuous."""
    assert REMOTE_DEPLOY_SCRIPT.is_file()
    assert SCRIPT.startswith("#!/usr/bin/env bash")
    subprocess.run(["bash", "-n", str(REMOTE_DEPLOY_SCRIPT)], check=True, capture_output=True)

    # It still carries the deploy logic the other contract tests assert on.
    for required in (
        "check_predeploy_runtime_contract.py",
        "check_runtime_http_surface.py",
        '--expected-commit "$TARGET_SHA"',
        "restore-proof.json",
        "rollback",
        "Build identity mismatch",
    ):
        assert required in SCRIPT, required


def test_the_script_is_never_streamed_into_bash_over_stdin() -> None:
    """A heredoc into `bash -s` is what let a truncated delivery read as a clean deploy.

    Scoped to the promotion step. The earlier proxy-inventory step still streams a script
    over stdin, but it runs before anything restarts and validates its own output — a
    truncated inventory yields an empty NUTEV_PROXY_MODE and fails the mode assertion — so
    it cannot produce the silent half-deploy this test exists to prevent.
    """
    run = _step("Deploy verified commit to Hetzner")["run"]
    # Comments in the step explain why the old form was abandoned; judge the code only.
    code = "\n".join(line for line in run.split("\n") if not line.strip().startswith("#"))
    assert "bash -s" not in code
    assert "<<'REMOTE'" not in WORKFLOW


def test_delivery_is_checksum_verified_before_execution() -> None:
    run = _step("Deploy verified commit to Hetzner")["run"]

    assert "sha256sum deploy/hetzner/remote_deploy.sh" in run
    assert "sha256sum -c -" in run

    # Order matters: the digest must be checked before the script is executed.
    verify_at = run.index("sha256sum -c -")
    execute_at = run.index("bash $REMOTE_SCRIPT_Q")
    assert verify_at < execute_at, "the digest check must precede execution"


def test_remote_script_ends_with_the_completion_sentinel() -> None:
    body = [line for line in SCRIPT.strip().split("\n") if line.strip() and not line.strip().startswith("#")]
    assert SENTINEL in body[-1], "the sentinel must be the script's final act"

    # Every failure path exits non-zero before reaching it, so the sentinel means
    # "ran to completion" rather than merely "reached the end of whatever arrived".
    assert "rollback; exit 1" in SCRIPT


def test_workflow_fails_the_deploy_when_the_sentinel_is_absent() -> None:
    run = _step("Deploy verified commit to Hetzner")["run"]

    assert f'grep -q "{SENTINEL} $TARGET_SHA"' in run
    assert "completion sentinel" in run
    # A clean ssh exit alone must not be accepted.
    assert 'SSH_STATUS="${PIPESTATUS[0]}"' in run
    assert "exit 1" in run


def test_post_promotion_evidence_is_collected_and_uploaded() -> None:
    names = [step.get("name") for step in _deploy_steps()]
    assert "Collect post-promotion deploy evidence" in names
    assert "Upload post-promotion deploy evidence" in names

    collect = _step("Collect post-promotion deploy evidence")
    upload = _step("Upload post-promotion deploy evidence")

    # Evidence must survive a failed deploy, which is exactly when it is most wanted.
    assert collect.get("if") == "always()"
    assert upload.get("if") == "always()"
    assert upload["with"]["path"] == "deploy-evidence/"

    # Collection runs after the deploy, never before it.
    names_in_order = [step.get("name") for step in _deploy_steps()]
    assert names_in_order.index("Deploy verified commit to Hetzner") < names_in_order.index(
        "Collect post-promotion deploy evidence"
    )


def test_remote_script_preserves_each_verification_artifact() -> None:
    """The JSON the checks produce must be kept, on the success and rollback paths alike."""
    for name in (
        "runtime-preflight.json",
        "http-preflight.json",
        "runtime-production.json",
        "http-production.json",
    ):
        assert f"keep_evidence /tmp/nutev-{name} {name}" in SCRIPT, name

    # The two production checks keep their evidence before rolling back.
    for source in ("/tmp/nutev-runtime-production.json", "/tmp/nutev-http-production.json"):
        rollback_line = next(
            line for line in SCRIPT.split("\n") if source in line and "rollback" in line
        )
        assert "keep_evidence" in rollback_line, source
        assert rollback_line.index("keep_evidence") < rollback_line.index("rollback")


def test_deploy_step_captures_its_own_session_log() -> None:
    run = _step("Deploy verified commit to Hetzner")["run"]
    assert "tee deploy-session.log" in run

    collect = _step("Collect post-promotion deploy evidence")["run"]
    assert "deploy-session.log" in collect, "the session log belongs in the evidence artifact"


def test_evidence_collection_cannot_turn_a_good_deploy_red() -> None:
    """Fetching evidence is observability, not a gate; it must not fail the promotion."""
    collect = _step("Collect post-promotion deploy evidence")["run"]
    assert "set -uo pipefail" in collect
    assert "set -euo pipefail" not in collect
    # The remote fetch and cleanup both tolerate a missing directory.
    assert re.search(r"tar -xf - -C deploy-evidence.*\|\| echo", collect, re.S)
    assert "rm -rf $EVIDENCE_DIR_Q\" || true" in collect


def test_evidence_directory_is_scoped_per_run() -> None:
    """Two runs must not read each other's evidence."""
    step = _step("Deploy verified commit to Hetzner")
    collect = _step("Collect post-promotion deploy evidence")
    for env in (step["env"], collect["env"]):
        assert "github.run_id" in env["EVIDENCE_DIR"]
        assert "github.run_attempt" in env["EVIDENCE_DIR"]
    assert step["env"]["EVIDENCE_DIR"] == collect["env"]["EVIDENCE_DIR"]


def test_deploy_still_changes_no_scientific_state() -> None:
    """Moving the script must not have smuggled in a scientific mutation."""
    for forbidden in (
        "press_status",
        "gf10_authorized",
        "query_freeze_complete",
        "prisma_search_event_emitted",
        "article1_search_master_v1.json",
    ):
        assert forbidden not in SCRIPT, forbidden
