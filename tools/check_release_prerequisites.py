"""Read-only, fail-closed release barrier for the current main SHA.

Only trusted GitHub Actions runs, exact workflow paths, successful required
jobs/steps and the latest run attempt count. No SSH or scientific operations.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

REQUIRED = {
    ".github/workflows/ci.yml": {
        "tests (python 3.12)": ("Run Reference Engine tests",),
        "tests (python 3.13)": ("Run Reference Engine tests",),
        "windows smoke (python 3.12)": ("CLI smoke", "Ranking smoke without network"),
        "typecheck provenance core": ("Mypy Reference Engine provenance core",),
        "lint (ruff)": ("Ruff blocking errors",),
        "audit guardrail contract": ("Run NutEV Scientific Closure death test",),
    },
    ".github/workflows/codeql.yml": {
        "CodeQL analyze (python)": ("Perform CodeQL Analysis",),
    },
    ".github/workflows/gitleaks.yml": {
        "gitleaks secret scan": ("Run gitleaks",),
        "forbidden files & large files": ("Check for forbidden committed files",),
    },
    ".github/workflows/predeploy-browser-e2e.yml": {
        "Chromium pre-deploy product gate": ("Run real Chromium pre-deploy audit",),
        "Authenticated pilot browser closeout": ("Run authenticated pilot browser matrix",),
    },
    ".github/workflows/dependency-review.yml": {
        "dependency-review": ("Dependency Review",),
    },
    ".github/workflows/release-artifact-validation.yml": {
        "build, twine check, clean wheel install": (
            "Build wheel and sdist", "Install wheel in a clean virtual environment",
        ),
    },
    ".github/workflows/multitenant-release-audit.yml": {
        "Full multi-tenant death test": (
            "Run hermetic death matrix", "Validate death matrix evidence",
        ),
    },
}
GetJSON = Callable[[str], dict[str, Any]]


class GateError(RuntimeError):
    """A safe diagnostic without API bodies, credentials or private payloads."""

    def __init__(self, code: str, *, retryable: bool = False):
        super().__init__(code)
        self.retryable = retryable


def _positive(value: Any) -> bool:
    return type(value) is int and value > 0


def validate_target(repo: str, sha: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise GateError("invalid_repository")
    if any(part in (".", "..") for part in repo.split("/")):
        raise GateError("invalid_repository")
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise GateError("invalid_target_sha")


def collection(get: GetJSON, path: str, key: str) -> list[dict[str, Any]]:
    """Bounded pagination; incomplete, duplicate or changing totals fail closed."""
    result: list[dict[str, Any]] = []
    seen: set[int] = set()
    expected = None
    sep = "&" if "?" in path else "?"
    for page in range(1, 11):
        data = get(f"{path}{sep}per_page=100&page={page}")
        total = data.get("total_count")
        items = data.get(key)
        if type(total) is not int or not 0 <= total <= 1000 or not isinstance(items, list):
            raise GateError("invalid_collection")
        if expected is not None and total != expected:
            raise GateError("collection_changed", retryable=True)
        expected = total
        if len(items) > 100:
            raise GateError("invalid_page_size")
        for item in items:
            if not isinstance(item, dict) or not _positive(item.get("id")):
                raise GateError("invalid_collection_item")
            if item["id"] in seen:
                raise GateError("duplicate_collection_item")
            seen.add(item["id"])
            result.append(item)
        if len(result) == total:
            return result
        if len(result) > total or not items:
            raise GateError("incomplete_collection")
    raise GateError("pagination_limit")


def _trusted(run: dict[str, Any], repo: str, sha: str) -> bool:
    return (
        run.get("head_sha") == sha
        and run.get("head_branch") == "main"
        and run.get("event") in ("push", "workflow_dispatch")
        and isinstance(run.get("repository"), dict)
        and run["repository"].get("full_name") == repo
        and isinstance(run.get("head_repository"), dict)
        and run["head_repository"].get("full_name") == repo
    )


def _main(get: GetJSON, sha: str) -> None:
    data = get("branches/main")
    if not isinstance(data.get("commit"), dict) or data["commit"].get("sha") != sha:
        raise GateError("target_is_not_current_main")


def inspect_release(get: GetJSON, repo: str, sha: str) -> dict[str, Any]:
    validate_target(repo, sha)
    _main(get, sha)
    params = urlencode({"head_sha": sha, "branch": "main"})
    runs = collection(get, f"actions/runs?{params}", "workflow_runs")
    selected = {}
    for path in REQUIRED:
        eligible = [r for r in runs if r.get("path") == path and _trusted(r, repo, sha)]
        if not eligible:
            raise GateError(f"missing_workflow:{path}", retryable=True)
        run = max(eligible, key=lambda r: r["id"])
        if run.get("status") != "completed":
            raise GateError(f"workflow_pending:{path}", retryable=True)
        if run.get("conclusion") != "success":
            raise GateError(f"workflow_not_success:{path}")
        if not _positive(run.get("run_attempt")):
            raise GateError("invalid_run_attempt")
        selected[path] = run
    evidence = []
    for path, run in selected.items():
        rid, attempt = run["id"], run["run_attempt"]
        jobs = collection(get, f"actions/runs/{rid}/attempts/{attempt}/jobs", "jobs")
        verified_jobs = []
        for name, required_steps in REQUIRED[path].items():
            matches = [j for j in jobs if j.get("name") == name]
            if len(matches) != 1:
                raise GateError(f"missing_or_duplicate_job:{path}:{name}")
            job = matches[0]
            if (job.get("run_id") != rid or job.get("head_sha") != sha
                    or job.get("status") != "completed" or job.get("conclusion") != "success"):
                raise GateError(f"job_not_success:{path}:{name}")
            steps = job.get("steps")
            if not isinstance(steps, list) or not all(isinstance(s, dict) for s in steps):
                raise GateError("invalid_job_steps")
            # Do not allow continue-on-error to hide a failed required job step.
            if any(s.get("conclusion") in ("failure", "cancelled", "timed_out", "action_required")
                   for s in steps):
                raise GateError(f"failed_step:{path}:{name}")
            for step_name in required_steps:
                matches_step = [s for s in steps if s.get("name") == step_name]
                if (len(matches_step) != 1 or matches_step[0].get("status") != "completed"
                        or matches_step[0].get("conclusion") != "success"):
                    raise GateError(f"required_step_not_success:{path}:{name}:{step_name}")
            verified_jobs.append({"id": job["id"], "name": name, "status": "PASS"})
        fresh = get(f"actions/runs/{rid}")
        if (not _trusted(fresh, repo, sha) or fresh.get("id") != rid
                or fresh.get("path") != path or fresh.get("run_attempt") != attempt
                or fresh.get("status") != "completed" or fresh.get("conclusion") != "success"):
            raise GateError(f"run_changed_during_verification:{path}")
        evidence.append({"workflow": path, "run_id": rid, "attempt": attempt, "jobs": verified_jobs})
    # Catch a newly dispatched run as well as a rerun of an existing run.
    final_runs = collection(get, f"actions/runs?{params}", "workflow_runs")
    for path, old in selected.items():
        eligible = [r for r in final_runs if r.get("path") == path and _trusted(r, repo, sha)]
        if not eligible:
            raise GateError(f"workflow_changed_during_verification:{path}")
        latest = max(eligible, key=lambda r: r["id"])
        if (latest.get("id") != old["id"] or latest.get("run_attempt") != old["run_attempt"]
                or latest.get("status") != "completed" or latest.get("conclusion") != "success"):
            raise GateError(f"workflow_changed_during_verification:{path}")
    _main(get, sha)
    return {
        "record_type": "NUTEV_RELEASE_PREREQUISITES", "schema_version": 1,
        "repository": repo, "sha": sha, "status": "PASS",
        "checked_at": datetime.now(timezone.utc).isoformat(), "workflows": evidence,
        "production_deployed": False, "scientific_state_modified": False,
    }


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise GateError("api_redirect_denied")


def api_reader(repo: str, token: str) -> GetJSON:
    opener = build_opener(NoRedirect())

    def get(path: str) -> dict[str, Any]:
        if not path.startswith(("branches/", "actions/")) or ".." in path or ":" in path:
            raise GateError("api_path_denied")
        request = Request(
            f"https://api.github.com/repos/{repo}/{path}",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                     "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "NutEV-release-gate"},
        )
        try:
            with opener.open(request, timeout=20) as response:
                body = response.read(5_000_001)
            if len(body) > 5_000_000:
                raise GateError("api_response_too_large")
            payload = json.loads(body)
        except HTTPError as exc:
            raise GateError(f"api_http_{exc.code}") from None
        except (URLError, TimeoutError, OSError, ValueError):
            raise GateError("api_response_unavailable") from None
        if not isinstance(payload, dict):
            raise GateError("api_response_not_object")
        return payload

    return get


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--wait-seconds", type=int, default=0, choices=range(0, 901), metavar="0..900")
    args = parser.parse_args()
    report: dict[str, Any] = {"record_type": "NUTEV_RELEASE_PREREQUISITES", "schema_version": 1,
                              "status": "FAIL", "sha": args.sha, "repository": args.repo,
                              "production_deployed": False, "scientific_state_modified": False}
    deadline = time.monotonic() + args.wait_seconds
    try:
        validate_target(args.repo, args.sha)
        token = os.environ.get("GITHUB_TOKEN", "")
        if not token:
            raise GateError("missing_read_only_github_token")
        get = api_reader(args.repo, token)
        while True:
            try:
                report = inspect_release(get, args.repo, args.sha)
                break
            except GateError as exc:
                if not exc.retryable or time.monotonic() >= deadline:
                    raise
                time.sleep(min(15, max(0, deadline - time.monotonic())))
    except GateError as exc:
        report["reason"] = str(exc)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
