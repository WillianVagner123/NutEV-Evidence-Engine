from __future__ import annotations

import csv
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from nutev.engine.events import emit_event, write_event
from nutev.search.base import ProviderResult
from nutev.search.checkpoint import query_hash
from nutev.search.crossref import search_crossref
from nutev.search.europepmc import search_europepmc
from nutev.search.openalex import search_openalex
from nutev.search.pubmed import PubMedClient


def _append_csv(path: Path, row: dict[str, Any], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        if not exists:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in fields})


def _optional_missing(provider: str) -> str | None:
    if provider == "google_pse" and not (os.environ.get("GOOGLE_API_KEY") and os.environ.get("GOOGLE_CSE_ID")):
        return "missing GOOGLE_API_KEY/GOOGLE_CSE_ID"
    if provider == "serpapi" and not os.environ.get("SERPAPI_API_KEY"):
        return "missing SERPAPI_API_KEY"
    if provider == "brave" and not os.environ.get("BRAVE_API_KEY"):
        return "missing BRAVE_API_KEY"
    return None


def _registry() -> dict[str, Callable[..., list[dict[str, Any]]]]:
    return {
        "europepmc": lambda q, limit, ctx: search_europepmc(q, page_size=limit),
        "openalex": lambda q, limit, ctx: search_openalex(q, per_page=limit),
        "crossref": lambda q, limit, ctx: search_crossref(q, rows=limit),
    }


def search_provider(
    *,
    provider: str,
    query: str,
    workstream: str,
    limit: int,
    checkpoint_dir: Path,
    resume: bool = False,
    logger: Any | None = None,
    run_id: str | None = None,
    logs_dir: Path | None = None,
    mode: str | None = None,
) -> ProviderResult:
    logs_dir = logs_dir or checkpoint_dir.parent
    qh = query_hash(provider, workstream, query)
    events_path = logs_dir / "run_events.jsonl"
    started = time.monotonic()

    def event(stage: str, message: str, *, kind: str = "progress", meta: dict[str, Any] | None = None) -> None:
        if not run_id:
            return
        write_event(
            emit_event(
                run_id,
                stage,
                message,
                event_kind=kind,
                provider=provider,
                meta_json={"workstream": workstream, "query_hash": qh, "query": query, **(meta or {})},
            ),
            events_path,
        )

    event("provider_started", f"Provider {provider} started")
    early_skip_error = _optional_missing(provider)
    if not early_skip_error and provider in {"google", "google_pse", "serpapi", "brave"}:
        early_skip_error = "optional provider not configured in canonical runtime"
    if early_skip_error:
        result = ProviderResult(provider, query, status="skipped", error=early_skip_error, meta={"query_hash": qh})
        event("provider_skipped", f"Provider {provider} skipped", kind="warning", meta={"reason": early_skip_error})
        duration = time.monotonic() - started
        perf_fields = ["run_id", "provider", "workstream", "queries_attempted", "queries_completed", "queries_failed", "rows_returned", "duration_seconds", "status"]
        _append_csv(logs_dir / "provider_performance.csv", {"run_id": run_id or "", "provider": provider, "workstream": workstream, "queries_attempted": 1, "queries_completed": 0, "queries_failed": 0, "rows_returned": 0, "duration_seconds": round(duration, 3), "status": "skipped"}, perf_fields)
        fail_fields = ["run_id", "timestamp", "provider", "workstream", "query_hash", "query", "stage", "error_type", "error_message", "recoverable", "fallback_used"]
        _append_csv(logs_dir / "provider_failures.csv", {"run_id": run_id or "", "timestamp": datetime.now(timezone.utc).isoformat(), "provider": provider, "workstream": workstream, "query_hash": qh, "query": query, "stage": "provider_skipped", "error_type": "skipped", "error_message": early_skip_error, "recoverable": True, "fallback_used": False}, fail_fields)
        return result

    try:
        if provider == "pubmed":
            result = PubMedClient().search(
                query,
                limit=limit,
                context={
                    "workstream": workstream,
                    "checkpoint_dir": checkpoint_dir,
                    "resume": resume,
                    "logger": logger,
                    "mode": mode,
                },
            )
        else:
            fn = _registry().get(provider)
            if fn is None:
                result = ProviderResult(provider, query, status="skipped", error="unsupported_provider", meta={"query_hash": qh})
            else:
                rows = fn(query, limit, {"workstream": workstream, "checkpoint_dir": checkpoint_dir}) or []
                result = ProviderResult(provider, query, rows=rows, total_returned=len(rows), status="completed", meta={"query_hash": qh})
    except Exception as exc:
        result = ProviderResult(provider, query, status="failed", error=str(exc), meta={"query_hash": qh})

    duration = time.monotonic() - started
    stage = "provider_completed" if result.status == "completed" else ("provider_partial" if result.status == "partial" else ("provider_skipped" if result.status == "skipped" else "provider_failed"))
    kind = "progress" if result.status == "completed" else "warning"
    event(stage, f"Provider {provider} {result.status}", kind=kind, meta={"total_found": result.total_found, "total_returned": result.total_returned, "error": result.error, "duration_seconds": round(duration, 3)})

    perf_fields = ["run_id", "provider", "workstream", "queries_attempted", "queries_completed", "queries_failed", "rows_returned", "duration_seconds", "status"]
    _append_csv(
        logs_dir / "provider_performance.csv",
        {
            "run_id": run_id or "",
            "provider": provider,
            "workstream": workstream,
            "queries_attempted": 1,
            "queries_completed": int(result.status == "completed"),
            "queries_failed": int(result.status == "failed"),
            "rows_returned": result.total_returned,
            "duration_seconds": round(duration, 3),
            "status": result.status,
        },
        perf_fields,
    )
    if result.status in {"failed", "partial", "skipped"}:
        fail_fields = ["run_id", "timestamp", "provider", "workstream", "query_hash", "query", "stage", "error_type", "error_message", "recoverable", "fallback_used"]
        _append_csv(
            logs_dir / "provider_failures.csv",
            {
                "run_id": run_id or "",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "provider": provider,
                "workstream": workstream,
                "query_hash": qh,
                "query": query,
                "stage": stage,
                "error_type": result.status,
                "error_message": result.error or "",
                "recoverable": True,
                "fallback_used": False,
            },
            fail_fields,
        )
    return result
