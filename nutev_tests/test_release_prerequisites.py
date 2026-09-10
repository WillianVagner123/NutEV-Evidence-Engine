"""Synthetic, network-free regression tests for release promotion boundaries."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("release_prerequisites", ROOT / "tools/check_release_prerequisites.py")
assert SPEC and SPEC.loader
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)
REPO = "fixture-owner/fixture-repo"
SHA = "a" * 40


class FakeAPI:
    def __init__(self):
        self.main_sha = SHA
        self.runs = []
        self.jobs = {}
        self.calls = []
        for index, (path, required) in enumerate(GATE.REQUIRED.items(), 1):
            run = {"id": index, "path": path, "head_sha": SHA, "head_branch": "main",
                   "repository": {"full_name": REPO}, "head_repository": {"full_name": REPO},
                   "event": "push", "status": "completed", "conclusion": "success", "run_attempt": 1}
            self.runs.append(run)
            self.jobs[index] = [
                {"id": index * 100 + n, "name": name, "run_id": index, "head_sha": SHA,
                 "status": "completed", "conclusion": "success", "steps": [
                     {"name": step, "status": "completed", "conclusion": "success"} for step in steps
                 ]} for n, (name, steps) in enumerate(required.items(), 1)
            ]

    def __call__(self, path):
        self.calls.append(path)
        if path == "branches/main":
            return {"commit": {"sha": self.main_sha}}
        url = urlsplit(path)
        parts = url.path.split("/")
        if url.path == "actions/runs":
            items, key = self.runs, "workflow_runs"
        elif len(parts) == 3:
            return copy.deepcopy(next(r for r in self.runs if r["id"] == int(parts[2])))
        else:
            assert parts[3:] == ["attempts", "1", "jobs"]
            items, key = self.jobs[int(parts[2])], "jobs"
        page = int(parse_qs(url.query)["page"][0])
        return {"total_count": len(items), key: copy.deepcopy(items[(page - 1) * 100:page * 100])}


def test_all_gates_success_does_not_claim_deployment():
    api = FakeAPI()
    result = GATE.inspect_release(api, REPO, SHA)
    assert result["status"] == "PASS"
    assert len(result["workflows"]) == len(GATE.REQUIRED)
    assert result["sha"] == SHA
    assert result["production_deployed"] is False
    assert result["scientific_state_modified"] is False
    assert api.calls[0] == api.calls[-1] == "branches/main"


@pytest.mark.parametrize("path", tuple(GATE.REQUIRED))
def test_each_missing_workflow_blocks(path):
    api = FakeAPI()
    api.runs = [r for r in api.runs if r["path"] != path]
    with pytest.raises(GATE.GateError, match="missing_workflow"):
        GATE.inspect_release(api, REPO, SHA)


@pytest.mark.parametrize("status,conclusion", [
    ("completed", "failure"), ("completed", "skipped"), ("completed", "neutral"),
    ("completed", "cancelled"), ("completed", "timed_out"),
    ("in_progress", None), ("queued", None), ("completed", None),
])
def test_non_success_workflow_blocks(status, conclusion):
    api = FakeAPI()
    api.runs[0].update(status=status, conclusion=conclusion)
    with pytest.raises(GATE.GateError):
        GATE.inspect_release(api, REPO, SHA)


@pytest.mark.parametrize("field,value", [
    ("event", "pull_request"), ("event", "pull_request_target"),
    ("head_branch", "feature"), ("head_sha", "b" * 40),
    ("repository", {"full_name": "other/repo"}),
    ("head_repository", {"full_name": "other/repo"}), ("head_repository", None),
])
def test_foreign_or_wrong_execution_cannot_satisfy_gate(field, value):
    api = FakeAPI()
    api.runs[0][field] = value
    with pytest.raises(GATE.GateError, match="missing_workflow"):
        GATE.inspect_release(api, REPO, SHA)


def test_manual_trigger_still_requires_every_workflow():
    api = FakeAPI()
    for run in api.runs:
        run["event"] = "workflow_dispatch"
    assert GATE.inspect_release(api, REPO, SHA)["status"] == "PASS"
    api.runs.pop()
    with pytest.raises(GATE.GateError, match="missing_workflow"):
        GATE.inspect_release(api, REPO, SHA)


def test_newer_failure_cannot_reuse_previous_success():
    api = FakeAPI()
    newer = copy.deepcopy(api.runs[0])
    newer.update(id=999, conclusion="failure")
    api.runs.append(newer)
    with pytest.raises(GATE.GateError, match="workflow_not_success"):
        GATE.inspect_release(api, REPO, SHA)


@pytest.mark.parametrize("field,value", [
    ("run_id", 999), ("head_sha", "b" * 40), ("conclusion", "skipped"),
    ("conclusion", "failure"), ("status", "in_progress"),
])
def test_required_job_must_match_run_sha_and_success(field, value):
    api = FakeAPI()
    api.jobs[1][0][field] = value
    with pytest.raises(GATE.GateError, match="job_not_success"):
        GATE.inspect_release(api, REPO, SHA)


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "skipped", "continue_on_error"])
def test_required_job_or_step_cannot_disappear_or_fail(mutation):
    api = FakeAPI()
    if mutation == "missing":
        api.jobs[1].pop(0)
    elif mutation == "duplicate":
        job = copy.deepcopy(api.jobs[1][0])
        job["id"] = 99999
        api.jobs[1].append(job)
    elif mutation == "skipped":
        api.jobs[1][0]["steps"][0]["conclusion"] = "skipped"
    else:
        api.jobs[1][0]["steps"].append({"name": "hidden failure", "conclusion": "failure"})
    with pytest.raises(GATE.GateError):
        GATE.inspect_release(api, REPO, SHA)


@pytest.mark.parametrize("when", ["before", "after"])
def test_stale_main_is_rejected(when):
    api = FakeAPI()
    calls = 0
    def read(path):
        nonlocal calls
        if path == "branches/main":
            calls += 1
            if when == "before" or calls == 2:
                return {"commit": {"sha": "b" * 40}}
        return api(path)
    with pytest.raises(GATE.GateError, match="target_is_not_current_main"):
        GATE.inspect_release(read, REPO, SHA)


def test_rerun_during_validation_invalidates_evidence():
    api = FakeAPI()
    def read(path):
        result = api(path)
        if path == "actions/runs/1":
            result["run_attempt"] = 2
        return result
    with pytest.raises(GATE.GateError, match="run_changed"):
        GATE.inspect_release(read, REPO, SHA)


@pytest.mark.parametrize("sha", ["main", "a" * 7, "a" * 39, "g" * 40, "a" * 40 + "\n"])
def test_invalid_sha_denied_without_network(sha):
    api = FakeAPI()
    with pytest.raises(GATE.GateError, match="invalid_target_sha"):
        GATE.inspect_release(api, REPO, sha)
    assert not api.calls


@pytest.mark.parametrize("repo", ["../repo", "owner/..", "a/b/c", "https://evil.test/a", "a/b?x"])
def test_invalid_repository_denied_without_network(repo):
    api = FakeAPI()
    with pytest.raises(GATE.GateError, match="invalid_repository"):
        GATE.inspect_release(api, repo, SHA)
    assert not api.calls


def test_pagination_does_not_stop_at_first_page():
    def get(path):
        page = int(parse_qs(urlsplit(path).query)["page"][0])
        return {"total_count": 101, "items": [{"id": i} for i in (range(1, 101) if page == 1 else [101])]}
    assert len(GATE.collection(get, "actions/example", "items")) == 101


@pytest.mark.parametrize("payload", [
    {"total_count": 2, "items": []}, {"total_count": 0, "items": [{"id": 1}]},
    {"total_count": 2, "items": [{"id": 1}, {"id": 1}]},
    {"total_count": 1, "items": [{"id": True}]}, {"total_count": 1001, "items": []},
    {"total_count": True, "items": []}, {"total_count": 1, "items": "invalid"},
])
def test_incomplete_or_malformed_pagination_denied(payload):
    with pytest.raises(GATE.GateError):
        GATE.collection(lambda _: payload, "actions/example", "items")


def test_changed_pagination_total_denied():
    def get(path):
        page = int(parse_qs(urlsplit(path).query)["page"][0])
        return {"total_count": 2 if page == 1 else 3, "items": [{"id": page}]}
    with pytest.raises(GATE.GateError, match="collection_changed"):
        GATE.collection(get, "actions/example", "items")


def test_new_run_dispatched_during_validation_invalidates_evidence():
    api = FakeAPI()
    lists = 0
    def read(path):
        nonlocal lists
        if urlsplit(path).path == "actions/runs":
            lists += 1
            if lists == 2:
                newer = copy.deepcopy(api.runs[0])
                newer.update(id=999, conclusion=None, status="queued")
                api.runs.append(newer)
        return api(path)
    with pytest.raises(GATE.GateError, match="workflow_changed"):
        GATE.inspect_release(read, REPO, SHA)


def test_redirect_is_denied():
    with pytest.raises(GATE.GateError, match="api_redirect_denied"):
        GATE.NoRedirect().redirect_request(None, None, 302, "", {}, "https://other.invalid")


def test_no_token_produces_failure_report(tmp_path, monkeypatch):
    import json
    import sys
    output = tmp_path / "report.json"
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(sys, "argv", ["gate", "--repo", REPO, "--sha", SHA, "--output", str(output)])
    assert GATE.main() == 1
    result = json.loads(output.read_text())
    assert result["status"] == "FAIL"
    assert result["reason"] == "missing_read_only_github_token"
