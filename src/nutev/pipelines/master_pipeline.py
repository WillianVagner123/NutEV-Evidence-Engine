from __future__ import annotations
from pathlib import Path
import pandas as pd

from nutev.settings import NutevSettings, load_json
from nutev.querypacks.builders import build_querypack
from nutev.search.openalex import search_openalex
from nutev.search.europepmc import search_europepmc
from nutev.search.pubmed import search_pubmed
from nutev.search.crossref import search_crossref
from nutev.search.official_sources import manifest_sources
from nutev.analysis.relevance import score_record, keep_candidate_for_download
from nutev.analysis import domains_busca1, domains_busca2a, domains_busca2b
from nutev.analysis.article3_framework import build_framework_signals
from nutev.analysis.synthesis import build_master_rows, build_questionnaire_candidates, build_framework_components, write_synthesis_outputs
from nutev.analysis.prisma import build_prisma_flow, export_prisma
from nutev.download.downloader import download_records
from nutev.extract.smart_extract import extract_document
from nutev.export.metadata_tables import write_metadata_csv, write_simple_csv
from nutev.export.rayyan import write_rayyan
from nutev.export.excel_writer import write_analysis_xlsx, write_excel_file
from nutev.export.logs import write_run_summary
from nutev.export.methods_writer import write_methods_docs
from nutev.export.qualification_writer import write_qualification_outputs
from nutev.engine.ids import make_run_id, make_document_id
from nutev.engine.job import create_search_case, create_search_job, write_search_case, write_search_job_snapshot
from nutev.engine.events import emit_event, write_event
from nutev.engine.artifacts import build_artifact_manifest

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


def _provider_map():
    return {
        "pubmed": lambda q: search_pubmed(q, retmax=18),
        "europepmc": lambda q: search_europepmc(q, page_size=18),
        "openalex": lambda q: search_openalex(q, per_page=12),
        "crossref": lambda q: search_crossref(q, rows=18),
    }


def _dedup_rows(rows: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for r in rows:
        key = (
            (r.get("source") or "").lower(),
            (r.get("title") or "").strip().lower(),
            (r.get("url") or "").strip().lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def _safe_provider_call(provider: str, fn, q: str, ws: str, logger) -> list[dict]:
    try:
        result = fn(q)
        if not isinstance(result, list):
            logger.warning("%s retornou tipo inesperado ws=%s query=%s tipo=%s", provider, ws, q, type(result).__name__)
            return []
        return result
    except BaseException as e:
        logger.warning("%s falhou ws=%s query=%s erro=%s", provider, ws, q, e)
        return []


def run_pipeline(settings: NutevSettings, workstreams: list[str], logger) -> dict[str, int]:
    run_id = make_run_id()
    search_case = create_search_case("NutMEV Deep Research", workstreams, settings.mode, DEFAULT_PRIORITY, since_days=settings.since_days, country_discovery=True, official_crawl=True, web_enabled=settings.web_enabled, browser_enabled=settings.browser_enabled, llm_enabled=settings.llm_enabled)
    search_job = create_search_job(search_case.case_id, run_id, cli_args=[])
    write_search_case(search_case, settings.output_dirs["07_logs"] / "search_case.json")
    write_event(emit_event(run_id, "discovery_started", "Pipeline discovery started"), settings.output_dirs["07_logs"] / "run_events.jsonl")

    taxonomy = load_json(settings.config_root / "keyword_taxonomy.json")
    scoring = load_json(settings.config_root / "scoring_rules.json")
    sources = load_json(settings.config_root / "official_sources_manifest.json")
    qpack = build_querypack(taxonomy, workstreams)

    provider_map = _provider_map()

    all_rows, extraction_manifest, all_manifest, artifact_inputs = [], [], [], []
    total_downloads = total_failed = total_ocr = 0

    for ws, queries in qpack.items():
        ws_cfg = taxonomy.get("workstreams", {}).get(ws, taxonomy.get("workstreams", {}).get("artigo3_framework", {}))
        source_priority = ws_cfg.get("source_priority", DEFAULT_PRIORITY)
        query_budget = min(len(queries), QUERY_BUDGET.get(ws, 32))

        logger.info("workstream=%s queries_geradas=%d", ws, len(queries))
        rows = []
        hits_by_provider = {}

        for q in queries[:query_budget]:
            for provider in source_priority:
                if provider == "official_web":
                    continue
                fn = provider_map.get(provider)
                if fn is None:
                    continue

                new_rows = _safe_provider_call(provider, fn, q, ws, logger)
                hits_by_provider[provider] = hits_by_provider.get(provider, 0) + len(new_rows)
                rows += new_rows

        try:
            official_rows = manifest_sources(sources, ws)
            hits_by_provider["official_web"] = len(official_rows)
            rows += official_rows
        except Exception as e:
            logger.warning("official_web falhou ws=%s erro=%s", ws, e)

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
        for m in manifest:
            m["document_id"] = make_document_id(m)
            artifact_inputs.append({"document_id": m["document_id"], "artifact_type": "pdf", "path": m.get("path", ""), "source_stage": "download", "status": "ok"})
        total_downloads += len(manifest)
        total_failed += len(failed)
        for f in failed:
            f["document_id"] = make_document_id(f)
            write_event(emit_event(run_id, "metadata_only_saved", "Download failed, metadata only saved", event_kind="warning", document_id=f["document_id"], meta_json={"url": f.get("url"), "reason": f.get("reason")}), settings.output_dirs["07_logs"] / "run_events.jsonl")

        write_simple_csv(all_manifest, settings.project_root / "03_corpus" / "download_manifest.csv")
        write_simple_csv(failed, settings.project_root / "03_corpus" / "failed_downloads.csv")

        ext_by_url = {}
        for m in manifest:
            e = extract_document(
                Path(m["path"]),
                settings.output_dirs["04_ocr_text"],
                settings.output_dirs["05_extraction"],
                logger,
            )
            extraction_manifest.append(e)
            total_ocr += int(e.get("used_ocr", False))
            if isinstance(m.get("url"), str):
                ext_by_url[m["url"]] = e
            if isinstance(m.get("resolved_url"), str):
                ext_by_url[m["resolved_url"]] = e

        for r in rows:
            url_key = r.get("url")
            if not isinstance(url_key, str):
                url_key = ""
            e = ext_by_url.get(url_key, {})
            r["file_path"] = e.get("file", "")
            r["ocr_status"] = "used" if e.get("used_ocr") else "not_used"
            r["extraction_status"] = e.get("extraction_status", "missing")
            if e.get("text_path"):
                r["extracted_text"] = Path(e["text_path"]).read_text(encoding="utf-8", errors="ignore")

        if ws == "busca1":
            rows = domains_busca1.apply_domain_rules(rows, load_json(settings.config_root / "domain_rules_busca1.json"))
        elif ws == "busca2a":
            rows = domains_busca2a.apply_domain_rules(rows, load_json(settings.config_root / "domain_rules_busca2a.json"))
        elif ws == "busca2b":
            rows = domains_busca2b.apply_domain_rules(rows, load_json(settings.config_root / "domain_rules_busca2b.json"))
        elif ws in {"a3", "artigo3_framework"}:
            rows = build_framework_signals(rows)

        write_analysis_xlsx(rows, settings.output_dirs["06_tables"] / f"analysis_{ws}.xlsx")
        all_rows += rows

    write_metadata_csv(all_rows, settings.output_dirs["02_metadata"] / "metadata_master.csv")
    write_rayyan(all_rows, settings.output_dirs["02_metadata"] / "rayyan_ready.csv")
    write_simple_csv(extraction_manifest, settings.output_dirs["05_extraction"] / "extraction_manifest.csv")

    master = build_master_rows(all_rows)
    write_synthesis_outputs(master, settings.output_dirs["06_tables"])

    q_items = build_questionnaire_candidates(master)
    fw_items = build_framework_components(master)

    write_excel_file(pd.DataFrame(q_items), settings.output_dirs["06_tables"] / "NUTEV_QUESTIONNAIRE_ITEM_CANDIDATES.xlsx")
    write_excel_file(pd.DataFrame(fw_items), settings.output_dirs["06_tables"] / "NUTEV_FRAMEWORK_COMPONENTS.xlsx")

    write_qualification_outputs(master, q_items, fw_items, settings.output_dirs["06_tables"], settings.output_dirs["08_docs"])
    write_methods_docs(settings.output_dirs["08_docs"])

    prisma = build_prisma_flow(master, all_manifest, extraction_manifest)
    export_prisma(prisma, settings.output_dirs["06_tables"] / "NUTEV_PRISMA_FLOW.xlsx", settings.output_dirs["07_logs"] / "prisma_flow.json")

    write_event(emit_event(run_id, "synthesis_completed", "Synthesis completed"), settings.output_dirs["07_logs"] / "run_events.jsonl")
    build_artifact_manifest(artifact_inputs, settings.output_dirs["07_logs"] / "artifact_manifest.csv")
    search_job.status = "completed"
    search_job.finished_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    write_search_job_snapshot(search_job, settings.output_dirs["07_logs"] / "search_job_snapshot.json", {"mode": settings.mode, "workstreams": workstreams, "providers_enabled": DEFAULT_PRIORITY, "configs_loaded": ["keyword_taxonomy.json", "scoring_rules.json", "official_sources_manifest.json"], "scoring_rules": scoring, "country_manifest": sources, "environment": {"web_enabled": settings.web_enabled, "browser_enabled": settings.browser_enabled, "llm_enabled": settings.llm_enabled}})

    summary = {
        "workstreams": workstreams,
        "records": len(all_rows),
        "downloads_ok": total_downloads,
        "downloads_failed": total_failed,
        "ocr_docs": total_ocr,
    }
    write_run_summary(settings.output_dirs["07_logs"] / "run_summary.json", summary)
    (settings.output_dirs["07_logs"] / "run_summary_pretty.txt").write_text(
        "\n".join(f"{k}: {v}" for k, v in summary.items()),
        encoding="utf-8",
    )
    return summary