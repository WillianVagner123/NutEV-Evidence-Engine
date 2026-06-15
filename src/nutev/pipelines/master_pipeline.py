from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import pandas as pd

from nutev.analysis import domains_busca1, domains_busca2a, domains_busca2b
from nutev.analysis.article3_framework import build_framework_signals
from nutev.analysis.nutev_classifier import classify_evidence
from nutev.analysis.prisma import build_prisma_flow, export_prisma
from nutev.analysis.relevance import keep_candidate_for_download, score_record
from nutev.analysis.synthesis import (
    build_framework_components,
    build_master_rows,
    build_questionnaire_candidates,
    write_synthesis_outputs,
)
from nutev.download.downloader import download_records
from nutev.engine.artifacts import build_artifact_manifest
from nutev.engine.events import emit_event, write_event
from nutev.engine.ids import make_document_id, make_run_id
from nutev.engine.job import (
    create_search_case,
    create_search_job,
    write_search_case,
    write_search_job_snapshot,
)
from nutev.export.audit_artifacts import write_audit_artifacts
from nutev.export.curation import curate_outputs
from nutev.export.excel_writer import write_analysis_xlsx, write_excel_file
from nutev.export.logs import write_run_summary
from nutev.export.metadata_tables import (
    write_article_data_csv,
    write_metadata_csv,
    write_simple_csv,
)
from nutev.export.methods_writer import write_methods_docs
from nutev.export.qualification_writer import write_qualification_outputs
from nutev.export.rayyan import write_rayyan
from nutev.extract.smart_extract import extract_document
from nutev.querypacks.builders import build_querypack
from nutev.querypacks.provider_queries import (
    build_provider_querypack,
    write_provider_querypack_audit,
)
from nutev.search.provider_orchestrator import search_provider
from nutev.settings import NutevSettings, load_json

QUERY_BUDGET = {
    "busca1": 32,
    "busca2a": 36,
    "busca2b": 36,
    "a3": 28,
    "artigo3_framework": 28,
}

DOWNLOAD_BUDGET = {
    "busca1": 320,
    "busca2a": 380,
    "busca2b": 380,
    "a3": 260,
    "artigo3_framework": 260,
}

DEFAULT_PRIORITY = ["pubmed", "europepmc", "openalex", "crossref", "official_web"]

_WHITESPACE_RE = re.compile(r"\s+")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def _provider_map():
    return {"pubmed": True, "europepmc": True, "openalex": True, "crossref": True}


def _as_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _normalize_doi(value: object) -> str:
    text = _as_text(value).lower()
    if not text:
        return ""
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if text.startswith(prefix):
            text = text[len(prefix) :]
    return text.strip().strip("/")


def _normalize_url(value: object) -> str:
    text = _as_text(value)
    if not text:
        return ""
    parsed = urlsplit(text)
    if not parsed.scheme or not parsed.netloc:
        return text.strip().rstrip("/").lower().removeprefix("www.")

    netloc = parsed.netloc.lower().removeprefix("www.")
    if parsed.scheme.lower() == "http" and netloc.endswith(":80"):
        netloc = netloc[:-3]
    if parsed.scheme.lower() == "https" and netloc.endswith(":443"):
        netloc = netloc[:-4]

    path = parsed.path.rstrip("/") or "/"
    return f"{netloc}{path}".rstrip("/")


def _normalize_title(value: object) -> str:
    text = _WHITESPACE_RE.sub(" ", _as_text(value).lower()).strip()
    return _NON_ALNUM_RE.sub(" ", text).strip()


def _normalize_year(value: object) -> str:
    text = _as_text(value)
    if not text:
        return ""
    try:
        year = int(float(text))
    except Exception:
        return ""
    return str(year)


def _hash_fallback(row: dict) -> str:
    payload = json.dumps(row, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]  # noqa: S324


def _canonical_article_key(row: dict) -> tuple[str, str]:
    doi = _normalize_doi(row.get("doi"))
    if doi:
        return "doi", doi

    pmid = _as_text(row.get("pmid")).lower()
    if pmid:
        return "pmid", pmid

    pmcid = _as_text(row.get("pmcid")).lower()
    if pmcid:
        return "pmcid", pmcid

    url = _normalize_url(
        row.get("final_url") or row.get("resolved_url") or row.get("original_url") or row.get("url")
    )
    if url:
        return "url", url

    title = _normalize_title(row.get("title"))
    year = _normalize_year(row.get("year"))
    if title and year:
        return "title_year", f"{title}|{year}"

    return "row_hash", _hash_fallback(row)


def _merge_article_rows(existing: dict, incoming: dict) -> dict:
    merged = dict(existing)
    for key, value in incoming.items():
        if value in (None, "", [], {}):
            continue
        if key in {"abstract", "snippet", "summary"} and len(str(value)) > len(str(merged.get(key) or "")):
            merged[key] = value
        elif not merged.get(key):
            merged[key] = value
    # Keep the stronger URL for capture. PMC and direct full-text URLs tend to
    # produce better artifacts than DOI landing pages.
    existing_url = str(merged.get("url") or "")
    incoming_url = str(incoming.get("url") or "")
    if incoming_url and (
        not existing_url
        or "pmc.ncbi.nlm.nih.gov" in incoming_url
        or incoming_url.lower().endswith(".pdf")
    ):
        merged["url"] = incoming_url
    providers = []
    for value in (merged.get("matched_providers"), merged.get("source_provider"), merged.get("source"), incoming.get("matched_providers"), incoming.get("source_provider"), incoming.get("source")):
        for part in str(value or "").split("|"):
            part = part.strip()
            if part and part not in providers:
                providers.append(part)
    merged["matched_providers"] = "|".join(providers)
    merged["source"] = merged.get("source") or incoming.get("source")
    return merged


def _dedup_rows(rows: list[dict]) -> list[dict]:
    by_key: dict[tuple[str, str], dict] = {}
    order: list[tuple[str, str]] = []
    for r in rows:
        key = _canonical_article_key(r)
        if key not in by_key:
            r = dict(r)
            provider = r.get("source_provider") or r.get("source")
            if provider and not r.get("matched_providers"):
                r["matched_providers"] = str(provider)
            by_key[key] = r
            order.append(key)
        else:
            by_key[key] = _merge_article_rows(by_key[key], r)
    return [by_key[key] for key in order]


def _safe_provider_call(provider: str, fn, q: str, ws: str, logger) -> list[dict]:
    try:
        result = fn(q)
        if not isinstance(result, list):
            logger.warning(
                "%s retornou tipo inesperado ws=%s query=%s tipo=%s",
                provider,
                ws,
                q,
                type(result).__name__,
            )
            return []
        return result
    except Exception as e:
        logger.warning("%s falhou ws=%s query=%s erro=%s", provider, ws, q, e)
        return []


def _split_supported_providers(
    source_priority: list[str],
    provider_map: dict,
) -> tuple[list[str], list[str]]:
    supported: list[str] = []
    unsupported: list[str] = []
    for provider in source_priority:
        if provider == "official_web" or provider in provider_map:
            supported.append(provider)
        else:
            unsupported.append(provider)
    return supported, unsupported


def _write_querypack_audit(
    qpack: dict[str, list[str]],
    logs_dir: Path,
) -> None:
    logs_dir.mkdir(parents=True, exist_ok=True)
    (logs_dir / "querypack_executed.json").write_text(
        json.dumps(qpack, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    rows = []
    for workstream, queries in qpack.items():
        for query_order, query_text in enumerate(queries, start=1):
            rows.append(
                {
                    "workstream": workstream,
                    "query_order": query_order,
                    "query_text": query_text,
                }
            )
    write_simple_csv(rows, logs_dir / "querypack_executed.csv")


def run_pipeline(settings: NutevSettings, workstreams: list[str], logger) -> dict[str, int]:
    run_id = make_run_id()
    search_case = create_search_case(
        "NutMEV Deep Research",
        workstreams,
        settings.mode,
        DEFAULT_PRIORITY,
        since_days=settings.since_days,
        country_discovery=True,
        official_crawl=True,
        web_enabled=settings.web_enabled,
        browser_enabled=settings.browser_enabled,
        llm_enabled=settings.llm_enabled,
    )
    search_job = create_search_job(search_case.case_id, run_id, cli_args=[])
    write_search_case(search_case, settings.output_dirs["07_logs"] / "search_case.json")
    write_event(
        emit_event(run_id, "discovery_started", "Pipeline discovery started"),
        settings.output_dirs["07_logs"] / "run_events.jsonl",
    )

    taxonomy = load_json(settings.config_root / "keyword_taxonomy.json")
    scoring = load_json(settings.config_root / "scoring_rules.json")
    sources = load_json(settings.config_root / "official_sources_manifest.json")
    ontology = load_json(settings.config_root / "nutev_ontology.json")
    evidence_lenses = load_json(settings.config_root / "evidence_lenses.json")
    source_registry = load_json(settings.config_root / "source_registry.json")
    provider_map = _provider_map()
    providers_declared_by_workstream: dict[str, list[str]] = {}
    providers_executed_by_workstream: dict[str, list[str]] = {}
    providers_unsupported_by_workstream: dict[str, list[str]] = {}
    qpack = build_querypack(taxonomy, workstreams)
    _write_querypack_audit(qpack, settings.output_dirs["07_logs"])

    for ws in workstreams:
        ws_cfg = taxonomy.get("workstreams", {}).get(
            ws,
            taxonomy.get("workstreams", {}).get("artigo3_framework", {}),
        )
        source_priority = ws_cfg.get("source_priority", DEFAULT_PRIORITY)
        supported_priority, unsupported_priority = _split_supported_providers(
            source_priority,
            provider_map,
        )
        providers_declared_by_workstream[ws] = source_priority
        providers_executed_by_workstream[ws] = supported_priority
        providers_unsupported_by_workstream[ws] = unsupported_priority

    provider_querypack = build_provider_querypack(
        taxonomy,
        workstreams,
        providers_executed_by_workstream,
    )
    write_provider_querypack_audit(
        provider_querypack,
        settings.output_dirs["07_logs"],
    )

    all_rows, extraction_manifest, all_manifest, artifact_inputs = [], [], [], []
    all_failed: list[dict] = []
    total_downloads = total_failed = total_ocr = 0
    provider_status_counts = {"completed": 0, "partial": 0, "failed": 0, "skipped": 0, "empty": 0}
    provider_rows = {provider: 0 for provider in ["pubmed", "europepmc", "openalex", "crossref", "official_web", "google_pse", "serpapi", "brave"]}

    for ws, queries in qpack.items():
        supported_priority = providers_executed_by_workstream.get(ws, DEFAULT_PRIORITY)
        unsupported_priority = providers_unsupported_by_workstream.get(ws, [])
        if unsupported_priority:
            logger.warning(
                "ws=%s providers_nao_suportados=%s",
                ws,
                unsupported_priority,
            )
        query_budget = min(len(queries), QUERY_BUDGET.get(ws, 32))

        logger.info("workstream=%s queries_geradas=%d", ws, len(queries))
        rows = []
        hits_by_provider = {}

        provider_queries = provider_querypack.get(ws, {})
        for provider in supported_priority:
            if provider == "official_web":
                continue
            if provider not in provider_map:
                continue
            for q in provider_queries.get(provider, [])[:query_budget]:
                result = search_provider(
                    provider=provider,
                    query=q,
                    workstream=ws,
                    limit=18 if provider != "openalex" else 12,
                    checkpoint_dir=settings.output_dirs["07_logs"] / "checkpoints",
                    resume=True,
                    logger=logger,
                    run_id=run_id,
                    logs_dir=settings.output_dirs["07_logs"],
                    mode=settings.mode,
                )
                provider_status_counts[result.status] = provider_status_counts.get(result.status, 0) + 1
                provider_rows[provider] = provider_rows.get(provider, 0) + len(result.rows)
                hits_by_provider[provider] = hits_by_provider.get(provider, 0) + len(result.rows)
                rows += result.rows

        official_result = search_provider(
            provider="official_web",
            query=ws,
            workstream=ws,
            limit=500,
            checkpoint_dir=settings.output_dirs["07_logs"] / "checkpoints",
            resume=True,
            logger=logger,
            run_id=run_id,
            logs_dir=settings.output_dirs["07_logs"],
            mode=settings.mode,
            context={"official_manifest": sources},
        )
        provider_status_counts[official_result.status] = provider_status_counts.get(official_result.status, 0) + 1
        provider_rows["official_web"] = provider_rows.get("official_web", 0) + len(official_result.rows)
        hits_by_provider["official_web"] = len(official_result.rows)
        rows += official_result.rows

        logger.info("ws=%s hits_por_provider=%s", ws, hits_by_provider)

        for r in rows:
            r["workstream"] = ws

        rows = _dedup_rows(rows)
        rows = [score_record(r, scoring, ws) for r in rows]
        rows = sorted(rows, key=lambda x: x.get("relevance_score", 0), reverse=True)

        rows_for_download = [r for r in rows if keep_candidate_for_download(r, ws)]
        rows_for_download = rows_for_download[:DOWNLOAD_BUDGET.get(ws, 320)]

        logger.info("ws=%s candidatos_download=%d", ws, len(rows_for_download))

        manifest, failed = download_records(
            rows_for_download,
            settings.output_dirs["03B_public_downloads"],
            settings.output_dirs["03C_official_docs"],
            logger,
        )

        all_manifest += manifest
        all_failed += failed
        for m in manifest:
            m["document_id"] = make_document_id(m)
            artifact_inputs.append(
                {
                    "document_id": m["document_id"],
                    "artifact_type": "pdf" if m.get("ext") == "pdf" else m.get("ext", "artifact"),
                    "path": m.get("path", ""),
                    "source_stage": "download",
                    "status": "ok",
                }
            )
        total_downloads += len(manifest)
        total_failed += len(failed)
        for f in failed:
            f["document_id"] = make_document_id(f)
            write_event(
                emit_event(
                    run_id,
                    "metadata_only_saved",
                    "Download failed, metadata only saved",
                    event_kind="warning",
                    document_id=f["document_id"],
                    meta_json={"url": f.get("url"), "reason": f.get("reason")},
                ),
                settings.output_dirs["07_logs"] / "run_events.jsonl",
            )

        write_simple_csv(all_manifest, settings.project_root / "03_corpus" / "download_manifest.csv")
        write_simple_csv(all_failed, settings.project_root / "03_corpus" / "failed_downloads.csv")

        ext_by_url = {}
        for m in manifest:
            try:
                e = extract_document(
                    Path(m["path"]),
                    settings.output_dirs["04_ocr_text"],
                    settings.output_dirs["05_extraction"],
                    logger,
                )
            except Exception as exc:
                logger.warning("extract falhou path=%s erro=%s", m.get("path"), exc)
                e = {"file": m.get("path", ""), "ext": m.get("ext", ""), "used_ocr": False, "ocr_failed_pages": "", "text_path": "", "chars": 0, "extraction_status": "failed", "reason": str(exc)}
            extraction_manifest.append(e)
            total_ocr += int(e.get("used_ocr", False))
            if isinstance(m.get("url"), str):
                ext_by_url[m["url"]] = e
            if isinstance(m.get("resolved_url"), str):
                ext_by_url[m["resolved_url"]] = e

        failed_by_url: dict[str, dict] = {}
        for f in failed:
            if isinstance(f.get("url"), str):
                failed_by_url[f["url"]] = f
            if isinstance(f.get("resolved_url"), str):
                failed_by_url[f["resolved_url"]] = f

        for r in rows:
            url_key = r.get("url")
            if not isinstance(url_key, str):
                url_key = ""
            e = ext_by_url.get(url_key, {})
            f = failed_by_url.get(url_key, {})
            r["file_path"] = e.get("file", "")
            r["ocr_status"] = "used" if e.get("used_ocr") else "not_used"
            r["extraction_status"] = e.get("extraction_status", "missing")
            r["failure_reason"] = f.get("reason", "")
            if e.get("text_path"):
                r["extracted_text"] = Path(e["text_path"]).read_text(
                    encoding="utf-8",
                    errors="ignore",
                )

        # Backward-compatible legacy enrichments
        if ws == "busca1":
            rows = domains_busca1.apply_domain_rules(rows, load_json(settings.config_root / "domain_rules_busca1.json"))
        elif ws == "busca2a":
            rows = domains_busca2a.apply_domain_rules(rows, load_json(settings.config_root / "domain_rules_busca2a.json"))
        elif ws == "busca2b":
            rows = domains_busca2b.apply_domain_rules(rows, load_json(settings.config_root / "domain_rules_busca2b.json"))
        elif ws in {"a3", "artigo3_framework"}:
            rows = build_framework_signals(rows)

        # New integrated global evidence layer: all records pass through shared classifier/lenses.
        rows = classify_evidence(rows, ontology, evidence_lenses)
        for r in rows:
            r["source_registry_version"] = source_registry.get("version", "")
            r["ontology_version"] = ontology.get("version", "")

        write_analysis_xlsx(rows, settings.output_dirs["06_tables"] / f"analysis_{ws}.xlsx")
        all_rows += rows

    write_metadata_csv(all_rows, settings.output_dirs["02_metadata"] / "metadata_master.csv")
    write_article_data_csv(all_rows, settings.output_dirs["02_metadata"] / "article_data.csv")
    write_rayyan(all_rows, settings.output_dirs["02_metadata"] / "rayyan_ready.csv")
    write_simple_csv(
        extraction_manifest,
        settings.output_dirs["05_extraction"] / "extraction_manifest.csv",
    )

    master = build_master_rows(all_rows)
    write_synthesis_outputs(master, settings.output_dirs["06_tables"])

    q_items = build_questionnaire_candidates(master)
    fw_items = build_framework_components(master)

    write_excel_file(
        pd.DataFrame(q_items),
        settings.output_dirs["06_tables"] / "NUTEV_QUESTIONNAIRE_ITEM_CANDIDATES.xlsx",
    )
    write_excel_file(
        pd.DataFrame(fw_items),
        settings.output_dirs["06_tables"] / "NUTEV_FRAMEWORK_COMPONENTS.xlsx",
    )

    write_qualification_outputs(
        master,
        q_items,
        fw_items,
        settings.output_dirs["06_tables"],
        settings.output_dirs["08_docs"],
    )
    write_methods_docs(settings.output_dirs["08_docs"], settings.output_dirs["07_logs"])

    global_df = pd.DataFrame(master)
    if not global_df.empty:
        lens_cols = [c for c in global_df.columns if c.startswith("lens_") or c in {"workstream", "document_id", "title", "domains", "outcomes", "evidence_lenses", "relevance_score"}]
        protocol_cols = [c for c in global_df.columns if c.startswith("domain_") or c.startswith("outcome_") or c in {"workstream", "document_id", "title", "evidence_type"}]
        write_excel_file(
            global_df[lens_cols].copy(),
            settings.output_dirs["06_tables"] / "NUTEV_GLOBAL_EVIDENCE_MATRIX.xlsx",
        )
        write_excel_file(
            global_df[protocol_cols].copy(),
            settings.output_dirs["06_tables"] / "NUTEV_PROTOCOL_TRANSLATION_MATRIX.xlsx",
        )

    prisma = build_prisma_flow(master, all_manifest, extraction_manifest)
    export_prisma(
        prisma,
        settings.output_dirs["06_tables"] / "NUTEV_PRISMA_FLOW.xlsx",
        settings.output_dirs["07_logs"] / "prisma_flow.json",
    )

    curation_summary = curate_outputs(all_rows, settings.output_dirs["10_curated"])
    # Run the audit engine explicitly and write the four NUTEV audit CSVs into
    # 06_tables. This used to be wired only through an import-time monkey-patch
    # (sitecustomize), which made the scientific metrics silently zero unless
    # src/ happened to be on sys.path. Calling it here makes the evidence
    # claims / recommendation candidates / conflicts part of every real run.
    audit_summary = write_audit_artifacts(all_rows, settings.output_dirs["06_tables"])

    write_event(
        emit_event(run_id, "synthesis_completed", "Synthesis completed"),
        settings.output_dirs["07_logs"] / "run_events.jsonl",
    )
    write_event(
        emit_event(
            run_id,
            "curation_completed",
            "Curated layer completed",
            meta_json=curation_summary,
        ),
        settings.output_dirs["07_logs"] / "run_events.jsonl",
    )
    build_artifact_manifest(
        artifact_inputs,
        settings.output_dirs["07_logs"] / "artifact_manifest.csv",
    )
    # provider_failures.csv is written incrementally by the search orchestrator
    # (see provider_orchestrator._append_csv) under 07_logs, so it is not
    # rebuilt here.
    partial_results = provider_status_counts.get("failed", 0) > 0 or provider_status_counts.get("partial", 0) > 0
    run_status = "failed" if not all_rows and provider_status_counts.get("failed", 0) and not provider_status_counts.get("completed", 0) else ("partial" if partial_results else "completed")
    search_job.status = run_status
    search_job.finished_at = datetime.now(timezone.utc)
    write_search_job_snapshot(
        search_job,
        settings.output_dirs["07_logs"] / "search_job_snapshot.json",
        {
            "mode": settings.mode,
            "workstreams": workstreams,
            "providers_enabled": DEFAULT_PRIORITY,
            "providers_declared_by_workstream": providers_declared_by_workstream,
            "providers_executed_by_workstream": providers_executed_by_workstream,
            "providers_unsupported_by_workstream": providers_unsupported_by_workstream,
            "configs_loaded": [
                "keyword_taxonomy.json",
                "scoring_rules.json",
                "official_sources_manifest.json",
            ],
            "querypack_files": [
                "07_logs/querypack_executed.json",
                "07_logs/querypack_executed.csv",
                "07_logs/provider_querypack_executed.json",
                "07_logs/provider_querypack_executed.csv",
            ],
            "scoring_rules": scoring,
            "country_manifest": sources,
            "environment": {
                "web_enabled": settings.web_enabled,
                "browser_enabled": settings.browser_enabled,
                "llm_enabled": settings.llm_enabled,
            },
        },
    )

    summary = {
        "workstreams": workstreams,
        "records": len(all_rows),
        "downloads_ok": total_downloads,
        "downloads_failed": total_failed,
        "ocr_docs": total_ocr,
        "curated_unique_documents": curation_summary["unique_documents"],
        "evidence_claims_total": audit_summary["evidence_claims_total"],
        "evidence_claims_supported": audit_summary["evidence_claims_supported"],
        "evidence_claims_needs_review": audit_summary["evidence_claims_needs_review"],
        "recommendation_candidates_total": audit_summary["recommendation_candidates_total"],
        "recommendation_candidates_ready_review": audit_summary["recommendation_candidates_ready_review"],
        "recommendation_candidates_insufficient_evidence": audit_summary["recommendation_candidates_insufficient_evidence"],
        "conflicting_evidence_total": audit_summary["conflicting_evidence_total"],
        "run_status": run_status,
        "providers_started": sum(provider_status_counts.values()),
        "providers_completed": provider_status_counts.get("completed", 0),
        "providers_partial": provider_status_counts.get("partial", 0),
        "providers_failed": provider_status_counts.get("failed", 0),
        "providers_skipped": provider_status_counts.get("skipped", 0),
        "providers_empty": provider_status_counts.get("empty", 0),
        "providers_unsupported_by_workstream": providers_unsupported_by_workstream,
        "provider_rows": provider_rows,
        "pubmed_rows": provider_rows.get("pubmed", 0),
        "europepmc_rows": provider_rows.get("europepmc", 0),
        "openalex_rows": provider_rows.get("openalex", 0),
        "crossref_rows": provider_rows.get("crossref", 0),
        "official_rows": provider_rows.get("official_web", 0),
        "google_rows": provider_rows.get("google_pse", 0),
        "partial_results": partial_results,
        "resume_used": True,
        "checkpoint_resume_used": True,
        "checkpoint_dir": str(settings.output_dirs["07_logs"] / "checkpoints"),
        "status": run_status,
    }
    write_run_summary(settings.output_dirs["07_logs"] / "run_summary.json", summary)
    (settings.output_dirs["07_logs"] / "run_summary_pretty.txt").write_text(
        "\n".join(f"{k}: {v}" for k, v in summary.items()),
        encoding="utf-8",
    )
    return summary
