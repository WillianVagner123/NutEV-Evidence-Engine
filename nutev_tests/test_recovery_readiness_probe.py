"""The recovery-readiness probe must survive a restart without ever guessing.

`production recovery readiness` runs on every push to main and prunes release
recovery state on the server. It protects the live release by reading the active
commit from /api/version. A deploy triggered by an earlier push restarts the
application, so that endpoint can be briefly unreachable while this job runs —
which once made the job fail on an unparseable empty body.

Two properties have to hold together, and only one of them is about convenience:

* a transient restart must not fail the job, and
* an endpoint that never answers must still fail it, because pruning without
  knowing which release is live could discard the recovery state of production.

The real step script is extracted from ci.yml and executed against a stubbed
`ssh`, so these assertions cover the shipped text rather than a paraphrase.
"""
from __future__ import annotations

from pathlib import Path
import stat
import subprocess
import textwrap

import yaml

ROOT = Path(__file__).resolve().parents[1]
CI = ROOT / ".github" / "workflows" / "ci.yml"
STEP_NAME = "Prune allowlisted recovery state with bounded complete retention"
LIVE_SHA = "a" * 40


def _step_script() -> str:
    workflow = yaml.safe_load(CI.read_text(encoding="utf-8"))
    for job in workflow["jobs"].values():
        for step in job.get("steps", []):
            if str(step.get("name") or "") == STEP_NAME:
                return str(step["run"])
    raise AssertionError(f"step {STEP_NAME!r} not found in ci.yml")


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def _stage(tmp_path: Path, *, failures_before_success: int, always_fail: bool) -> Path:
    """Build a working directory where the step can run against a fake server."""

    work = tmp_path / "work"
    (work / "tools").mkdir(parents=True)
    (work / "tools" / "release_recovery_hygiene.py").write_text("# stub\n", encoding="utf-8")
    (work / "failed-deploy-shas.txt").write_text("", encoding="utf-8")
    (work / "complete-prune-shas.txt").write_text("", encoding="utf-8")

    stubs = tmp_path / "stubs"
    stubs.mkdir()
    counter = tmp_path / "attempts"
    counter.write_text("0", encoding="utf-8")

    # The probe reaches the server through ssh; the stub stands in for both the
    # reachability of the host and the application's availability behind it.
    _write_executable(
        stubs / "ssh",
        textwrap.dedent(
            f"""\
            #!/usr/bin/env bash
            remote="${{@: -1}}"
            if [[ "$remote" == *curl* ]]; then
              n=$(<"{counter}")
              echo $((n + 1)) > "{counter}"
              if [[ "{str(always_fail).lower()}" == "true" ]] \\
                 || (( n < {failures_before_success} )); then
                echo "curl: (7) Failed to connect" >&2
                exit 7
              fi
              printf '{{"commit": "{LIVE_SHA}"}}\\n'
              exit 0
            fi
            cat > /dev/null
            printf '{{"status": "PASS", "retain_complete": 3, '
            printf '"scientific_data_modified": false, "pruned_complete": [], '
            printf '"preserved_complete": 5}}\\n'
            """
        ),
    )
    # A real 10s backoff would make the failure case take four minutes.
    _write_executable(stubs / "sleep", "#!/usr/bin/env bash\nexit 0\n")
    return work


def _run(tmp_path: Path, work: Path) -> subprocess.CompletedProcess:
    script = work / "step.sh"
    script.write_text(_step_script(), encoding="utf-8")
    return subprocess.run(
        ["bash", str(script)],
        cwd=work,
        env={
            "PATH": f"{tmp_path / 'stubs'}:/usr/bin:/bin",
            "HETZNER_HOST": "host.invalid",
            "HETZNER_USER": "operator",
            "HETZNER_PORT": "22",
            "TARGET_SHA": "b" * 40,
        },
        capture_output=True,
        text=True,
    )


def test_probe_recovers_from_a_restart_window(tmp_path: Path) -> None:
    work = _stage(tmp_path, failures_before_success=4, always_fail=False)
    result = _run(tmp_path, work)

    assert result.returncode == 0, result.stdout + result.stderr
    assert f"active_release_sha={LIVE_SHA}" in result.stdout
    assert "not answering yet" in result.stdout, "the retries should be visible in the log"
    assert (work / "recovery-hygiene.json").exists()


def test_probe_still_fails_closed_when_the_endpoint_never_answers(tmp_path: Path) -> None:
    work = _stage(tmp_path, failures_before_success=0, always_fail=True)
    result = _run(tmp_path, work)

    assert result.returncode != 0
    assert "Refusing to prune recovery state" in result.stderr
    # Nothing may be pruned when the live release is unknown.
    assert not (work / "recovery-hygiene.json").exists()


def test_probe_is_bounded_rather_than_infinite(tmp_path: Path) -> None:
    work = _stage(tmp_path, failures_before_success=0, always_fail=True)
    _run(tmp_path, work)

    attempts = int((tmp_path / "attempts").read_text(encoding="utf-8").strip())
    assert 1 < attempts <= 24, f"probe attempted {attempts} times; expected a bounded retry"


def test_probe_rejects_a_reply_that_is_not_a_commit_sha(tmp_path: Path) -> None:
    """A malformed answer must be treated as no answer, never adopted."""

    work = _stage(tmp_path, failures_before_success=0, always_fail=False)
    _write_executable(
        tmp_path / "stubs" / "ssh",
        textwrap.dedent(
            """\
            #!/usr/bin/env bash
            remote="${@: -1}"
            if [[ "$remote" == *curl* ]]; then
              printf '{"commit": "unknown"}\\n'
              exit 0
            fi
            cat > /dev/null
            printf '{"status": "PASS"}\\n'
            """
        ),
    )
    result = _run(tmp_path, work)

    assert result.returncode != 0
    assert "Refusing to prune recovery state" in result.stderr


def test_ci_workflow_still_parses_and_the_step_is_reachable() -> None:
    """Guard the guard: a renamed step would make every assertion above vacuous."""

    assert "for attempt in" in _step_script()
    assert "--protect-sha" in _step_script()
