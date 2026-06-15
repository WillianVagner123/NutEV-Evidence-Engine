from __future__ import annotations

import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from nutev import __version__
from nutev.engine.ids import make_case_id, make_job_id
from nutev.engine.models import SearchCase, SearchJob


def _git_commit() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        return None


def create_search_case(name: str, workstreams: list[str], mode: str, providers_enabled: list[str], **kwargs) -> SearchCase:
    return SearchCase(
        case_id=make_case_id(),
        name=name,
        workstreams=workstreams,
        mode=mode,
        providers_enabled=providers_enabled,
        created_at=datetime.now(timezone.utc),
        **kwargs,
    )


def create_search_job(case_id: str, run_id: str, cli_args: list[str]) -> SearchJob:
    return SearchJob(job_id=make_job_id(), case_id=case_id, run_id=run_id, started_at=datetime.now(timezone.utc), git_commit=_git_commit(), cli_args=cli_args)


def write_search_case(search_case: SearchCase, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(search_case.model_dump_json(indent=2), encoding="utf-8")


def write_search_job_snapshot(search_job: SearchJob, path: Path, snapshot: dict) -> None:
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "package_version": __version__,
        "git_commit": search_job.git_commit,
        **snapshot,
        "search_job": search_job.model_dump(mode="json"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
