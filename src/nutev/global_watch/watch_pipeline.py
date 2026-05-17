from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from nutev.engine.events import emit_event, write_event
from nutev.engine.ids import make_document_id, make_run_id
from nutev.engine.job import (
    create_search_case,
    create_search_job,
    write_search_case,
    write_search_job_snapshot,
)
from nutev.global_watch.watch_capture import capture_watch_items
from nutev.global_watch.watch_diff import (
    load_seen_items,
    mark_new_items,
    save_seen_items,
    update_seen_items,
)
from nutev.global_watch.watch_digest import write_digest
from nutev.global_watch.watch_export import export_watch_outputs
from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item
from nutev.global_watch.watch_webhook import maybe_send_webhook
from nutev.search.europepmc import search_europepmc
from nutev.search.openalex import search_openalex
from nutev.search.pubmed import search_pubmed
from nutev.settings import load_json

try:
    from nutev.search.crossref import search_crossref
except Exception:  # pragma: no cover
    search_crossref = None

try:
    from nutev.search.official_sources import manifest_sources
except Exception:  # pragma: no cover
    manifest_sources = None


def _provider_query(base: str, provider: str, since_days: int) -> str:
    date_from = (
        datetime.now(timezone.utc).date() - timedelta(days=max(since_days, 0))
    ).isoformat()
    if provider == "pubmed":
        return (
            f"({base}) AND (\"{date_from}\"[Date - Publication] : "
            f"\"3000\"[Date - Publication])"
        )
    if provider == "europepmc":
        return f"({base}) AND FIRST_PDATE:[{date_from} TO *]"
    if provider == "openalex":
        return f"{base} from_publication_date:{date_from}"
    if provider == "crossref":
        return f"{base} from-pub-date:{date_from}"
    return base


def infer_evidence_type(title: str, abstract: str, url: str) -> str:
    text = f"{title} {abstract} {url}".lower()
    if "guideline" in text or "diretriz" in text:
        return "guideline"
    if "consensus" in text or "scientific statement" in text:
        return "consensus"
    if "systematic review" in text or "meta-analysis" in text:
        return "systematic_review"
    if "trial" in text:
        return "trial"
    return "study"


def infer_workstream_affinity(title: str, category: str) -> list[str]:
    text = f"{title} {category}".lower()
    workstreams: list[str] = []
    if any(
        keyword in text for keyword in ["guideline", "diet", "food", "nutrition"]
    ):
        workstreams.append("busca1")
    if any(
        keyword in text
        for keyword in ["obesity", "cardio", "metabolic", "diabetes"]
    ):
        workstreams.append("busca2a")
    if any(
        keyword in text
        for keyword in [
            "adherence",
            "implementation",
            "behavior",
            "framework",
            "instrument",
        ]
    ):
        workstreams.append("busca2b")
    if any(
        keyword in text for keyword in ["framework", "questionnaire", "competencies"]
    ):
        workstreams.append("a3")
    if workstreams:
        return workstreams
    return ["busca1"]


def normalize_watch_hit(
    raw_hit: dict,
    provider_name: str,
    category: str,
    query: str,
    since_days: int = 30,
) -> dict[str, Any]:
    title = raw_hit.get("title") or ""
    year = raw_hit.get("year")
    try:
        year = int(year) if year is not None else None
    except Exception:
        year = None

    is_recent = bool(
        year
        and year
        >= datetime.now(timezone.utc).year - (1 if since_days <= 365 else 2)
    )
    item = {
        "title": title,
        "url": raw_hit.get("url") or "",
        "doi": raw_hit.get("doi") or "",
        "year": year,
        "source_provider": provider_name,
        "category": category,
        "query": query,
        "evidence_type": infer_evidence_type(
            title,
            raw_hit.get("abstract") or "",
            raw_hit.get("url") or "",
        ),
        "workstream_affinity": infer_workstream_affinity(title, category),
        "download_status": "metadata_only",
        "relevance_score": 50,
        "failure_reason": "",
        "fallback_used": False,
        "is_recent_publication": is_recent,
    }
    item["document_id"] = make_document_id(item)
    return item


def _build_provider_map() -> dict[str, Any]:
    provider_map: dict[str, Any] = {
        "pubmed": lambda query: search_pubmed(query, retmax=12),
        "europepmc": lambda query: search_europepmc(query, page_size=12),
        "openalex": lambda query: search_openalex(query, per_page=10),
    }
    if search_crossref:
        provider_map["crossref"] = lambda query: search_crossref(query, rows=10)
    return provider_map


def run_watch_provider(
    provider_name: str,
    query: str,
    category: str,
    logger,
    run_id: str,
    logs_dir: Path,
    since_days: int,
) -> list[dict[str, Any]]:
    write_event(
        emit_event(
            run_id,
            "provider_started",
            f"Provider {provider_name} started",
            provider=provider_name,
            meta_json={"category": category},
        ),
        logs_dir / "run_events.jsonl",
    )
    filtered_query = _provider_query(query, provider_name, since_days)
    provider_fn = _build_provider_map().get(provider_name)
    if provider_fn is None:
        write_event(
            emit_event(
                run_id,
                "provider_disabled",
                f"Provider {provider_name} unavailable",
                event_kind="warning",
                provider=provider_name,
            ),
            logs_dir / "run_events.jsonl",
        )
        return []
    try:
        rows = provider_fn(filtered_query) or []
        out = [
            normalize_watch_hit(r, provider_name, category, query, since_days)
            for r in rows
        ]
        write_event(
            emit_event(
                run_id,
                "provider_completed",
                f"Provider {provider_name} completed",
                provider=provider_name,
                meta_json={"hits": len(out)},
            ),
            logs_dir / "run_events.jsonl",
        )
        return out
    except Exception as exc:
        logger.warning(
            "provider_failed provider=%s query=%s error=%s",
            provider_name,
            query,
            exc,
        )
        write_event(
            emit_event(
                run_id,
                "provider_failed",
                f"Provider {provider_name} failed",
                event_kind="warning",
                provider=provider_name,
                meta_json={"error": str(exc)},
            ),
            logs_dir / "run_events.jsonl",
        )
        return []


def run_global_watch(
    settings,
    logger,
    since_days,
    mode,
    resume,
    official_crawl,
    country_discovery,
    llm_enabled,
    capture_enabled=False,
    capture_limit=None,
    notify_webhook=False,
    webhook_url=None,
):
    run_id = make_run_id()
    logs = settings.output_dirs["07_logs"]
    case = create_search_case(
        "NutMEV Global Watch",
        ["global_watch"],
        "watch",
        ["pubmed", "europepmc", "openalex", "crossref", "official_sources"],
        since_days=since_days,
        official_crawl=official_crawl,
        country_discovery=country_discovery,
        web_enabled=settings.web_enabled,
        llm_enabled=llm_enabled,
    )
    job = create_search_job(case.case_id, run_id, [])
    write_search_case(case, logs / "search_case.json")
    write_event(
        emit_event(run_id, "global_watch_started", "Global watch started"),
        logs / "run_events.jsonl",
    )
    if llm_enabled and not os.getenv("OPENAI_API_KEY"):
        write_event(
            emit_event(
                run_id,
                "llm_disabled",
                "OPENAI_API_KEY not found",
                event_kind="warning",
            ),
            logs / "run_events.jsonl",
        )

    queries = build_watch_queries([], since_days, mode)
    providers = ["pubmed", "europepmc", "openalex", "crossref"]
    rows: list[dict[str, Any]] = []
    query_limit = 8 if mode == "quick" else 20 if mode == "thesis" else 30
    for query_item in queries[:query_limit]:
        for provider in providers:
            rows.extend(
                run_watch_provider(
                    provider,
                    query_item["query"],
                    query_item["category"],
                    logger,
                    run_id,
                    logs,
                    since_days,
                )
            )

    if official_crawl and manifest_sources is not None:
        try:
            manifest = load_json(
                settings.config_root / "official_sources_manifest.json"
            )
            for ws in ["busca1", "busca2a", "busca2b", "a3"]:
                for record in manifest_sources(manifest, ws):
                    rows.append(
                        normalize_watch_hit(
                            record,
                            "official_sources",
                            "guidelines_consensus",
                            "official manifest",
                            since_days,
                        )
                    )
        except Exception as exc:
            write_event(
                emit_event(
                    run_id,
                    "provider_failed",
                    "official_sources failed",
                    event_kind="warning",
                    provider="official_sources",
                    meta_json={"error": str(exc)},
                ),
                logs / "run_events.jsonl",
            )

    if not rows:
        fallback = normalize_watch_hit(
            {
                "title": "global watch fallback item",
                "url": "https://fallback.local",
                "doi": "",
            },
            "watch_seed",
            "guidelines_consensus",
            "fallback",
            since_days,
        )
        fallback["fallback_used"] = True
        fallback["failure_reason"] = "no_provider_results"
        rows = [fallback]

    rows = list({row["document_id"]: row for row in rows}.values())
    seen_path = (
        settings.project_root / "09_global_watch" / "watch_state" / "seen_items.json"
    )
    seen = load_seen_items(seen_path) if resume else {}
    rows = mark_new_items(rows, seen)
    for row in rows:
        row["is_new_to_system"] = bool(row.get("is_new"))
        row["novelty_score"] = 1.0 if row.get("is_new") else 0.2
        row["watch_score"] = score_watch_item(row)
    rows.sort(key=lambda item: item.get("watch_score", 0), reverse=True)
    save_seen_items(seen_path, update_seen_items(rows, seen))

    captured_items: list[dict[str, Any]] = []
    if capture_enabled:
        rows, captured_items = capture_watch_items(
            rows,
            settings,
            logger,
            run_id,
            mode,
            capture_limit=capture_limit,
        )

    run_dir = (
        settings.project_root
        / "09_global_watch"
        / "runs"
        / datetime.now(timezone.utc).date().isoformat()
    )
    new_rows = [row for row in rows if row.get("is_new")]
    host_failures = [
        {
            "host": row.get("host", ""),
            "failure_reason": row.get("failure_reason", ""),
            "http_status": row.get("http_status", ""),
        }
        for row in rows
        if row.get("failure_reason")
    ]
    provider_perf = []
    for provider in providers:
        provider_rows = [
            row for row in rows if row.get("source_provider") == provider
        ]
        provider_perf.append(
            {
                "provider": provider,
                "hits": len(provider_rows),
                "captured": sum(
                    1
                    for row in provider_rows
                    if row.get("download_status") in {"pdf", "html_snapshot"}
                ),
            }
        )
    capture_manifest = [
        {
            "document_id": row.get("document_id"),
            "download_status": row.get("download_status"),
            "capture_status": row.get("capture_status"),
            "artifact_paths": row.get("artifact_paths", {}),
        }
        for row in captured_items
    ]
    digest_md, _ = write_digest(
        rows,
        run_dir,
        settings.output_dirs["08_docs"] / "NUTEV_GLOBAL_WATCH_LATEST.md",
    )
    summary = {
        "mode": mode,
        "total_items": len(rows),
        "new_items": len(new_rows),
        "high_priority": sum(
            1 for row in rows if (row.get("watch_score") or 0) >= 80
        ),
        "pdf": sum(1 for row in rows if row.get("download_status") == "pdf"),
        "html_snapshot": sum(
            1 for row in rows if row.get("download_status") == "html_snapshot"
        ),
        "metadata_only": sum(
            1 for row in rows if row.get("download_status") == "metadata_only"
        ),
        "failed": sum(
            1 for row in rows if row.get("download_status") == "failed"
        ),
    }
    webhook_result = maybe_send_webhook(
        rows,
        digest_md,
        summary,
        settings,
        logger,
        run_id,
        enabled=notify_webhook,
        webhook_url=webhook_url,
    )
    included_ids = {row.get("document_id") for row in rows[:10]}
    for row in rows:
        row["webhook_included"] = (
            row.get("document_id") in included_ids
            and webhook_result.get("status") == "sent"
        )
    export_watch_outputs(
        rows,
        new_rows,
        settings.project_root / "09_global_watch",
        run_dir,
        provider_perf=provider_perf,
        host_failures=host_failures,
        capture_manifest=capture_manifest,
    )
    job.status = "completed"
    job.finished_at = datetime.now(timezone.utc)
    write_search_job_snapshot(
        job,
        logs / "search_job_snapshot.json",
        {"mode": mode, "since_days": since_days, "resume": resume, "providers": providers},
    )
    write_event(
        emit_event(
            run_id,
            "global_watch_completed",
            "Global watch completed",
        ),
        logs / "run_events.jsonl",
    )
    return {"rows": len(rows), "new_items": len(new_rows)}
