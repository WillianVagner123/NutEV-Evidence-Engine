from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from nutev.analysis import domains_busca1, domains_busca2a, domains_busca2b
from nutev.analysis.article3_framework import build_framework_signals
from nutev.analysis.dedup import (
    as_text,
    canonical_article_key,
    dedup_rows,
    hash_fallback,
    merge_article_rows,
    normalize_doi,
    normalize_title,
    normalize_url,
    normalize_year,
)
from nutev.analysis.nutev_classifier import classify_evidence
from nutev.analysis.prisma import build_prisma_flow, export_prisma
from nutev.analysis.relevance import keep_candidate_for_download, score_record
from nutev.analysis.synthesis import (
    build_framework_components,
    build_master_rows,
    build_questionnaire_candidates,
    write_synthesis_outputs,
)
from nutev.config_provenance import write_config_provenance
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
from nutev.export.citations import write_bibtex, write_ris
from nutev.export.curation import curate_outputs
from nutev.export.curation_finalize import audit_metrics, finalize_curated_layer
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
from nutev.search.official_sources import load_official_manifest
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

def _provider_map():
    return {"pubmed": True, "europepmc": True, "openalex": True, "crossref": True}


# Deduplication moved to nutev.analysis.dedup (kept importable here under the
# historical private names so the pipeline call sites and existing test imports —
# e.g. `from nutev.pipelines.master_pipeline import _dedup_rows, _normalize_url` —
# keep working unchanged).
_as_text = as_text
_normalize_doi = normalize_doi
_normalize_url = normalize_url
_normalize_title = normalize_title
_normalize_year = normalize_year
_hash_fallback = hash_fallback
_canonical_article_key = canonical_article_key
_merge_article_rows = merge_article_rows
_dedup_rows = dedup_rows


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
    # Guarantee the runtime-compat hooks (incl. the audit/claims stage) are in
    # place no matter how run_pipeline is reached — not only via cli.main. Before
    # this, calling run_pipeline directly (e.g. embedded/programmatic use) skipped
    # apply() and produced zero claims/recommendations. apply() is idempotent, so
    # this is a no-op when the CLI already applied it. (Removing the shim layer
    # entirely is a separate, larger refactor: it also injects scientific query
    # terms and is relied on across the test suite, so it must not be rushed.)
    try:
        from nutev.runtime_compat import apply as _apply_runtime_compat

        _apply_runtime_compat()
    except Exception:
        logger.debug("runtime_compat apply skipped", exc_info=True)

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
    # Base official-source manifest merged with the global per-country/region
    # manifest (all countries) — see docs/PILOT_AUDIT_RESPONSE.md.
    sources = load_official_manifest(settings.config_root, include_countries=True)
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
            # Only feed genuinely-extracted text downstream. Junk/blocked/too-thin
            # pages must NOT reach the classifier, dietary-pattern detection or
            # claim extractor (they previously polluted classification and
            # produced spurious "supported" claims).
            if e.get("text_path") and e.get("extraction_status") in {
                "ok",
                "ok_ocr",
                "fake_pdf_html",
                "fake_pdf_text",
            }:
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

    # Enrich every row with the Article 1 analytical fields (track, provenance,
    # A/B/C/D domains, AACODS, archive hash) and the key phrases BEFORE any table
    # is written, so the primary metadata/article CSVs and every downstream table
    # carry the coding and key sentences. Assistive; enters human review
    # (docs/ARTICLE1_DOMAIN_CODING.md). Failures never abort a run.
    # Classified failures are recorded, not swallowed: if an enrichment stage
    # fails, the whole run silently loses that column — so we log it AND record
    # the lost coverage (07_logs/coverage_loss.json) instead of `except: pass`.
    from nutev.telemetry.coverage import CoverageLog, write_coverage_report

    coverage = CoverageLog()
    try:
        from nutev.analysis.article1_coding import article1_record_fields

        for _row in all_rows:
            _row.update(article1_record_fields(_row))
    except Exception as exc:  # never abort a run — but never hide the loss
        logger.warning("codificação A/B/C/D falhou: %s", exc)
        coverage.record_exception(exc, code="artifact_contract_error", component="article1_coding",
                                  stage="enrichment", impact="corpus sem colunas A/B/C/D/track")
    try:
        from nutev.analysis.keyphrases import keyphrase_fields

        for _row in all_rows:
            _kp = keyphrase_fields(_row)
            _row["key_phrases_text"] = _kp["key_phrases_text"]
            _row["n_key_phrases"] = _kp["n_key_phrases"]
            _row["top_terms"] = _kp["top_terms"]
    except Exception as exc:
        logger.warning("frases-chave falharam: %s", exc)
        coverage.record_exception(exc, code="artifact_contract_error", component="keyphrases",
                                  stage="enrichment", impact="corpus sem frases-chave/top_terms")
    # The reference itself (citation string + structured fields), so every row —
    # and its key phrases — is traceable to its exact source, not just the text.
    try:
        from nutev.analysis.references import build_reference

        for _row in all_rows:
            _row.update(build_reference(_row))
    except Exception as exc:
        logger.warning("referências falharam: %s", exc)
        coverage.record_exception(exc, code="artifact_contract_error", component="references",
                                  stage="enrichment", impact="corpus sem coluna reference")
    # Rich thematic detection (diet patterns, LM pillars, neuro/mental, eating
    # competencies, processing, implementation) + doc type / evidence weight +
    # nutrition values. Only the flat, CSV-safe fields are attached here.
    try:
        from nutev.analysis.thematic import load_taxonomy, thematic_fields

        _taxonomy = load_taxonomy(settings.config_root)
        for _row in all_rows:
            _tf = thematic_fields(_row, _taxonomy)
            for _key in (
                "themes_present", "n_themes", "diet_patterns", "doc_type",
                "evidence_weight", "nutrition_macros_pct", "nutrition_fiber_g",
                "nutrition_sodium", "nutrition_micronutrients",
            ):
                _row[_key] = _tf[_key]
    except Exception as exc:
        logger.warning("detecção temática falhou: %s", exc)
        coverage.record_exception(exc, code="artifact_contract_error", component="thematic",
                                  stage="enrichment", impact="corpus sem colunas temáticas/nutrição")
    _coverage_summary = write_coverage_report(coverage, settings.output_dirs["07_logs"])

    write_metadata_csv(all_rows, settings.output_dirs["02_metadata"] / "metadata_master.csv")
    write_article_data_csv(all_rows, settings.output_dirs["02_metadata"] / "article_data.csv")
    write_rayyan(all_rows, settings.output_dirs["02_metadata"] / "rayyan_ready.csv")
    # Reference-manager exports (Zotero/Mendeley/EndNote): closes the
    # "registro recuperado → referência correspondente" link. Never invents data.
    write_bibtex(all_rows, settings.output_dirs["02_metadata"] / "NUTEV_REFERENCES.bib")
    write_ris(all_rows, settings.output_dirs["02_metadata"] / "NUTEV_REFERENCES.ris")
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
    # First-class audit + legacy finalization (was runtime_compat._patch_curation):
    # NUTEV_* renames, QA/PRISMA legacy reports, and the audit + convergence stage.
    finalize_curated_layer(all_rows, settings.output_dirs["10_curated"], curation_summary)
    claims = []
    recommendations = []
    conflicts = []

    # Article 1 central artifact: the Domain Integration Matrix (A/B/C/D coverage)
    # and the two-track PRISMA identification split. Coding is assistive and enters
    # human review (see docs/ARTICLE1_DOMAIN_CODING.md); failures never abort a run.
    article1_summary: dict = {}
    try:
        from nutev.export.article1_reports import (
            build_two_track_prisma,
            write_integration_matrix,
        )

        article1_summary = write_integration_matrix(all_rows, settings.output_dirs["06_tables"])
        article1_summary["prisma_two_track"] = build_two_track_prisma(all_rows)
    except Exception as exc:  # pragma: no cover - defensive
        article1_summary = {"article1_report_error": str(exc)}

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
    partial_results = provider_status_counts.get("failed", 0) > 0 or provider_status_counts.get("partial", 0) > 0
    run_status = "failed" if not all_rows and provider_status_counts.get("failed", 0) and not provider_status_counts.get("completed", 0) else ("partial" if partial_results else "completed")
    search_job.status = run_status
    search_job.finished_at = __import__("datetime").datetime.now(
        __import__("datetime").timezone.utc
    )
    # Pin the exact taxonomy/scoring configuration to this run (base + every
    # merged supplement, each hashed) so the result is reproducible and citable.
    config_provenance = write_config_provenance(
        settings.output_dirs["07_logs"] / "config_provenance.json",
        settings.config_root,
    )
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
            "config_digest": config_provenance["config_digest"],
            "configs_loaded": [
                source["name"]
                for family in config_provenance["families"].values()
                for source in family["sources"]
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

    # Real extracted-text accounting from the extraction manifest. Anti-bot /
    # redirect / too-thin pages are downgraded by the extractor and must NOT be
    # counted as extracted text (they previously inflated the corpus silently).
    _success_extraction = {"ok", "ok_ocr", "fake_pdf_html", "fake_pdf_text"}
    extracted_texts = sum(
        1 for e in extraction_manifest if e.get("extraction_status") in _success_extraction
    )
    extraction_junk_or_blocked = sum(
        1
        for e in extraction_manifest
        if e.get("extraction_status") in {"junk_or_blocked", "too_short"}
    )
    # Scanned/image-only PDFs that could not be read because the OCR
    # prerequisites (documents extra + poppler + tesseract) are not installed.
    extraction_pdf_needs_ocr_setup = sum(
        1
        for e in extraction_manifest
        if e.get("extraction_status") == "pdf_needs_ocr_setup"
    )

    summary = {
        "workstreams": workstreams,
        "records": len(all_rows),
        "downloads_ok": total_downloads,
        "downloads_failed": total_failed,
        "ocr_docs": total_ocr,
        "extracted_texts": extracted_texts,
        "extraction_junk_or_blocked": extraction_junk_or_blocked,
        "extraction_pdf_needs_ocr_setup": extraction_pdf_needs_ocr_setup,
        "curated_unique_documents": curation_summary["unique_documents"],
        # Claim/recommendation metrics come from the audit artifacts written
        # during curation (curation_summary), falling back to the local lists.
        # "supported" means quote-backed (verbatim quote found in extracted
        # text) — NOT scientifically validated. It still requires human review.
        "evidence_claims_total": curation_summary.get("evidence_claims_total", len(claims)),
        "evidence_claims_supported": curation_summary.get("evidence_claims_supported", sum(1 for c in claims if c.claim_status == "supported")),
        "evidence_claims_inference_only": curation_summary.get("evidence_claims_inference_only", sum(1 for c in claims if c.claim_status == "inference_only")),
        "evidence_claims_needs_review": curation_summary.get("evidence_claims_needs_review", sum(1 for c in claims if c.needs_human_review)),
        "recommendation_candidates_total": curation_summary.get("recommendation_candidates_total", len(recommendations)),
        "recommendation_candidates_ready_review": curation_summary.get("recommendation_candidates_ready_review", sum(1 for r in recommendations if r.recommendation_status == "ready_for_human_review")),
        "recommendation_candidates_insufficient_evidence": curation_summary.get("recommendation_candidates_insufficient_evidence", sum(1 for r in recommendations if r.recommendation_status == "insufficient_evidence")),
        "conflicting_evidence_total": curation_summary.get("conflicting_evidence_total", len(conflicts)),
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
    # Article 1 domain-integration metrics (domain_coverage, profile_distribution,
    # documents_with_all_four_domains, prisma_two_track).
    summary.update(article1_summary)
    # Lost-coverage accounting: what (if anything) an enrichment stage dropped.
    summary["coverage_loss"] = _coverage_summary

    # Full-text coverage (P6): how much full text this run actually captured per
    # workstream, plus the offline recoverability ceiling (OA vs paywall). Both
    # are computed offline — from the extraction status already on each row and
    # the identifiers in the metadata — so no network call is made here, and the
    # recoverability report is written to 07_logs. Never aborts a run.
    try:
        from nutev.acquire.recoverability import (
            diagnose_recoverability,
            fulltext_coverage_block,
            write_recoverability_outputs,
        )

        recover = diagnose_recoverability(all_rows)
        write_recoverability_outputs(recover, settings.output_dirs["07_logs"])
        summary.update(fulltext_coverage_block(all_rows, recoverability=recover))
    except Exception as exc:  # pragma: no cover - defensive; never abort a run
        summary["fulltext_coverage_error"] = str(exc)

    # Merge audit metrics from the written CSVs (was runtime_compat._patch_run_summary):
    # a truthy CSV-derived count wins, and any missing key is filled in.
    for key, value in audit_metrics(settings.output_dirs["02_metadata"]).items():
        if value or key not in summary:
            summary[key] = value

    write_run_summary(settings.output_dirs["07_logs"] / "run_summary.json", summary)
    (settings.output_dirs["07_logs"] / "run_summary_pretty.txt").write_text(
        "\n".join(f"{k}: {v}" for k, v in summary.items()),
        encoding="utf-8",
    )
    return summary
