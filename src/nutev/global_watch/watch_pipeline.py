from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import os

from nutev.engine.events import emit_event, write_event
from nutev.engine.ids import make_document_id, make_run_id
from nutev.engine.job import create_search_case, create_search_job, write_search_case, write_search_job_snapshot
from nutev.search.pubmed import search_pubmed
from nutev.search.europepmc import search_europepmc
from nutev.search.openalex import search_openalex
from nutev.global_watch.watch_diff import load_seen_items, mark_new_items, save_seen_items, update_seen_items
from nutev.global_watch.watch_digest import write_digest
from nutev.global_watch.watch_export import export_watch_outputs
from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item
from nutev.global_watch.watch_capture import capture_watch_items
from nutev.global_watch.watch_webhook import maybe_send_webhook
from nutev.settings import load_json

try:
    from nutev.search.crossref import search_crossref
except Exception:  # pragma: no cover
    search_crossref = None

try:
    from nutev.search.official_sources import manifest_sources
except Exception:  # pragma: no cover
    manifest_sources = None


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
    out = []
    if any(k in text for k in ["guideline", "diet", "food", "nutrition"]):
        out.append("busca1")
    if any(k in text for k in ["obesity", "cardio", "metabolic", "diabetes"]):
        out.append("busca2a")
    if any(k in text for k in ["adherence", "implementation", "behavior", "framework", "instrument"]):
        out.append("busca2b")
    if any(k in text for k in ["framework", "questionnaire", "competencies"]):
        out.append("a3")
    return out or ["busca1"]


def normalize_watch_hit(raw_hit: dict, provider_name: str, category: str, query: str) -> dict:
    title = raw_hit.get("title") or ""
    url = raw_hit.get("url") or ""
    doi = raw_hit.get("doi") or ""
    year = raw_hit.get("year")
    abstract = raw_hit.get("abstract") or ""
    item = {
        "title": title,
        "url": url,
        "doi": doi,
        "year": year,
        "source_provider": provider_name,
        "category": category,
        "query": query,
        "evidence_type": infer_evidence_type(title, abstract, url),
        "workstream_affinity": infer_workstream_affinity(title, category),
        "download_status": "metadata_only",
        "relevance_score": 50,
        "failure_reason": "",
        "fallback_used": False,
    }
    item["document_id"] = make_document_id(item)
    return item


def run_watch_provider(provider_name: str, query: str, category: str, logger, run_id: str, logs_dir: Path) -> list[dict]:
    write_event(emit_event(run_id, "provider_started", f"Provider {provider_name} started", provider=provider_name, meta_json={"category": category}), logs_dir / "run_events.jsonl")
    provider_fn = {
        "pubmed": lambda q: search_pubmed(q, retmax=12),
        "europepmc": lambda q: search_europepmc(q, page_size=12),
        "openalex": lambda q: search_openalex(q, per_page=10),
        "crossref": (lambda q: search_crossref(q, rows=10)) if search_crossref else None,
    }.get(provider_name)
    if provider_name == "official_sources":
        if manifest_sources is None:
            write_event(emit_event(run_id, "provider_disabled", "official_sources unavailable", event_kind="warning", provider=provider_name), logs_dir / "run_events.jsonl")
            return []
        return []
    if provider_fn is None:
        write_event(emit_event(run_id, "provider_disabled", f"Provider {provider_name} unavailable", event_kind="warning", provider=provider_name), logs_dir / "run_events.jsonl")
        return []
    try:
        rows = provider_fn(query) or []
        out = [normalize_watch_hit(r, provider_name, category, query) for r in rows]
        write_event(emit_event(run_id, "provider_completed", f"Provider {provider_name} completed", provider=provider_name, meta_json={"hits": len(out)}), logs_dir / "run_events.jsonl")
        return out
    except Exception as exc:
        logger.warning("provider_failed provider=%s query=%s error=%s", provider_name, query, exc)
        write_event(emit_event(run_id, "provider_failed", f"Provider {provider_name} failed", event_kind="warning", provider=provider_name, meta_json={"error": str(exc)}), logs_dir / "run_events.jsonl")
        return []


def run_global_watch(settings, logger, since_days, mode, resume, official_crawl, country_discovery, llm_enabled, capture_enabled=False, capture_limit=None, notify_webhook=False, webhook_url=None):
    run_id = make_run_id()
    logs = settings.output_dirs["07_logs"]
    case = create_search_case("NutMEV Global Watch", ["global_watch"], "watch", ["pubmed", "europepmc", "openalex", "crossref", "official_sources"], since_days=since_days, official_crawl=official_crawl, country_discovery=country_discovery, web_enabled=settings.web_enabled, llm_enabled=llm_enabled)
    job = create_search_job(case.case_id, run_id, [])
    write_search_case(case, logs / "search_case.json")
    write_event(emit_event(run_id, "global_watch_started", "Global watch started"), logs / "run_events.jsonl")
    if llm_enabled and not os.getenv("OPENAI_API_KEY"):
        write_event(emit_event(run_id, "llm_disabled", "OPENAI_API_KEY not found", event_kind="warning"), logs / "run_events.jsonl")

    queries = build_watch_queries([], since_days, mode)
    providers = ["pubmed", "europepmc", "openalex", "crossref"]
    rows = []
    for q in queries[:8 if mode == "quick" else 20 if mode == "thesis" else 30]:
        for provider in providers:
            rows.extend(run_watch_provider(provider, q["query"], q["category"], logger, run_id, logs))

    if official_crawl and manifest_sources is not None:
        try:
            manifest = load_json(settings.config_root / "official_sources_manifest.json")
            for ws in ["busca1", "busca2a", "busca2b", "a3"]:
                for r in manifest_sources(manifest, ws):
                    rows.append(normalize_watch_hit(r, "official_sources", "guidelines_consensus", "official manifest"))
        except Exception as exc:
            write_event(emit_event(run_id, "provider_failed", "official_sources failed", event_kind="warning", provider="official_sources", meta_json={"error": str(exc)}), logs / "run_events.jsonl")

    if not rows:
        fallback = normalize_watch_hit({"title": "global watch fallback item", "url": "https://fallback.local", "doi": ""}, "watch_seed", "guidelines_consensus", "fallback")
        fallback["fallback_used"] = True
        fallback["failure_reason"] = "no_provider_results"
        rows = [fallback]

    dedup = {r["document_id"]: r for r in rows}
    rows = list(dedup.values())
    seen_path = settings.project_root / "09_global_watch" / "watch_state" / "seen_items.json"
    seen = load_seen_items(seen_path) if resume else {}
    rows = mark_new_items(rows, seen)
    for r in rows:
        r["novelty_score"] = 1.0 if r.get("is_new") else 0.2
        r["watch_score"] = score_watch_item(r)
    rows.sort(key=lambda x: x.get("watch_score", 0), reverse=True)
    save_seen_items(seen_path, update_seen_items(rows, seen))

    if capture_enabled:
        rows, captured_items = capture_watch_items(rows, settings, logger, run_id, mode)
        if capture_limit:
            captured_items = captured_items[:capture_limit]
    else:
        captured_items = []

    run_dir = settings.project_root / "09_global_watch" / "runs" / datetime.now(timezone.utc).date().isoformat()
    new_rows = [r for r in rows if r.get("is_new")]
    host_failures = [{"host": r.get("host",""), "failure_reason": r.get("failure_reason",""), "http_status": r.get("http_status","")} for r in rows if r.get("failure_reason")]
    provider_perf = []
    for p in providers:
        pr = [r for r in rows if r.get("source_provider")==p]
        provider_perf.append({"provider": p, "hits": len(pr), "captured": sum(1 for x in pr if x.get("download_status") in {"pdf","html_snapshot"})})
    capture_manifest=[{"document_id":r.get("document_id"),"download_status":r.get("download_status"),"capture_status":r.get("capture_status"),"artifact_paths":r.get("artifact_paths",{})} for r in captured_items]
    digest_md, _ = write_digest(rows, run_dir, settings.output_dirs["08_docs"] / "NUTEV_GLOBAL_WATCH_LATEST.md")
    summary = {"mode": mode, "total_items": len(rows), "new_items": len(new_rows), "high_priority": sum(1 for r in rows if (r.get("watch_score") or 0) >= 80), "pdf": sum(1 for r in rows if r.get("download_status")=="pdf"), "html_snapshot": sum(1 for r in rows if r.get("download_status")=="html_snapshot"), "metadata_only": sum(1 for r in rows if r.get("download_status")=="metadata_only"), "failed": sum(1 for r in rows if r.get("download_status")=="failed")}
    wh = maybe_send_webhook(rows, digest_md, summary, settings, logger, run_id, enabled=notify_webhook, webhook_url=webhook_url)
    included_ids = {r.get("document_id") for r in rows[:10]}
    for r in rows: r["webhook_included"] = r.get("document_id") in included_ids and wh.get("status") == "sent"
    export_watch_outputs(rows, new_rows, settings.project_root / "09_global_watch", run_dir, provider_perf=provider_perf, host_failures=host_failures, capture_manifest=capture_manifest)
    job.status = "completed"
    job.finished_at = datetime.now(timezone.utc)
    write_search_job_snapshot(job, logs / "search_job_snapshot.json", {"mode": mode, "since_days": since_days, "resume": resume, "providers": providers})
    write_event(emit_event(run_id, "global_watch_completed", "Global watch completed"), logs / "run_events.jsonl")
    return {"rows": len(rows), "new_items": len(new_rows)}
