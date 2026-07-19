"""Guides pipeline (Track 1): fetch ALL official guides, OCR, code, key-phrase.

This is the end-to-end "pegar todos os guias" flow, run directly over the full
~140-source country manifest (no relevance budget, no database indexing) so every
guide is attempted:

    load manifest -> fetch (provenance) -> extract/OCR -> A/B/C/D coding -> key phrases

It reuses the existing pieces natively — :mod:`nutev.acquire.guias_fetcher`
(fetch + provenance), :func:`nutev.extract.smart_extract.extract_document`
(OCR), :func:`nutev.analysis.article1_coding.article1_record_fields` (coding),
:func:`nutev.analysis.keyphrases.keyphrase_fields`. Nothing is fabricated and no
paywall is bypassed; all coding is assistive and enters human review.

The HTTP session is injected so the run is testable/rate-limitable. When no
session is given (offline), fetching is skipped and any PDFs already present in
the official-docs directory are still extracted, coded and key-phrased.
"""
from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from nutev.acquire.guias_fetcher import fetch_guide, load_guide_sources
from nutev.analysis.article1_coding import article1_record_fields
from nutev.analysis.domain_states import code_domain_states, domain_state_rows
from nutev.analysis.evidence_gems import best_gems_markdown, rank_gems
from nutev.analysis.keyphrases import (
    extract_keyphrases_from_pages,
    top_terms,
)
from nutev.analysis.references import build_reference
from nutev.analysis.registries import build_registries
from nutev.review.screening import build_screening_queue
from nutev.analysis.thematic import evidence_rows, load_taxonomy, thematic_fields
from nutev.export.metadata_tables import write_simple_csv
from nutev.extract.smart_extract import extract_document

_FULLTEXT_OK = {"ok", "ok_ocr", "fake_pdf_html", "fake_pdf_text"}

# Columns written to the coded-guides table (flat, human-readable).
_TABLE_COLUMNS = (
    "name", "country", "institution", "source_url", "access_date",
    "fulltext_status", "archived_pdf_path", "sha256", "archived_pdf_sha256",
    "aacods_authority_tier", "track", "doc_type", "evidence_weight",
    "extraction_status", "used_ocr", "chars",
    "profile", "n_domains", "domain_A", "domain_B", "domain_C", "domain_D",
    "domain_A_state", "domain_A_intensity", "domain_B_state", "domain_B_intensity",
    "domain_C_state", "domain_C_intensity", "domain_D_state", "domain_D_intensity",
    "domain_coding_source",
    "diet_patterns", "n_themes", "themes_present",
    "nutrition_macros_pct", "nutrition_fiber_g", "nutrition_sodium", "nutrition_micronutrients",
    "reference", "n_key_phrases", "top_terms", "key_phrases_text",
)


def _extracted_text_for(extraction: dict) -> str:
    """Read the extracted text file, only for genuinely-usable extractions."""
    path = extraction.get("text_path")
    if path and extraction.get("extraction_status") in _FULLTEXT_OK:
        try:
            return Path(path).read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""
    return ""


def process_guide(record: dict, settings, logger) -> dict:
    """Extract/OCR one fetched guide, code A/B/C/D, and pull key phrases.

    ``record`` is a provenance record from ``guias_fetcher.fetch_guide``. Returns
    a flat row combining provenance + extraction + coding + key phrases.
    """
    row = dict(record)
    pdf_path = record.get("archived_pdf_path") or ""
    extraction: dict = {"extraction_status": "no_file", "used_ocr": False, "chars": 0, "text_path": "", "pages": []}
    if pdf_path and Path(pdf_path).is_file():
        try:
            extraction = extract_document(
                Path(pdf_path),
                settings.output_dirs["04_ocr_text"],
                settings.output_dirs["05_extraction"],
                logger,
                capture_pages=True,
            )
        except Exception as exc:  # never abort the batch on one bad file
            logger.warning("extract falhou guia=%s erro=%s", pdf_path, exc)
            extraction = {"extraction_status": "failed", "used_ocr": False, "chars": 0, "text_path": "", "pages": []}

    row["extraction_status"] = extraction.get("extraction_status", "")
    row["used_ocr"] = bool(extraction.get("used_ocr", False))
    row["chars"] = int(extraction.get("chars", 0) or 0)
    row["extracted_text"] = _extracted_text_for(extraction)

    # A/B/C/D coding + provenance/AACODS (assistive; enters human review).
    row.update(article1_record_fields(row))
    # The reference itself (citation string + structured fields) so every key
    # phrase is traceable to its exact source, not just the text.
    row.update(build_reference(row))

    # Rich thematic detection (diet patterns, LM pillars, neuro/mental, eating
    # competencies, processing, implementation) + evidence snippets + doc type /
    # evidence weight + nutrition values. Config-driven; failures never abort.
    try:
        row.update(thematic_fields(row, load_taxonomy(settings.config_root)))
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("detecção temática falhou guia=%s erro=%s", row.get("name"), exc)

    # Protocol domain states + intensity (0–3) with page-precise evidence
    # (§7.2/§7.3) — a machine SUGGESTION beside the A/B/C/D booleans; two humans
    # decide. Never asserts absence.
    pages = extraction.get("pages") or ([row["extracted_text"]] if row["extracted_text"].strip() else [])
    row.update(code_domain_states(row, pages=pages))

    # Page-precise key phrases: each carries its source page AND the reference.
    phrases = extract_keyphrases_from_pages(pages)
    reference = row.get("reference", "")
    for phrase in phrases:
        phrase["reference"] = reference
        phrase["source_url"] = row.get("reference_url", "")
        phrase["sha256"] = row.get("reference_sha256", "")
    row["key_phrases"] = phrases
    row["n_key_phrases"] = len(phrases)
    row["top_terms"] = "|".join(top_terms(row["extracted_text"]))
    # Human-readable block: [A] (p.3) sentence — Reference
    row["key_phrases_text"] = "\n".join(
        f"[{p['domain']}] (p.{p['page']}) {p['sentence']}" for p in phrases
    )
    return row


def _guide_key(source_or_row: dict) -> str:
    """Stable identity for save/continue: URL first, else name+country, else path."""
    url = str(source_or_row.get("source_url") or source_or_row.get("url") or "").strip()
    if url:
        return f"url:{url}"
    name = str(source_or_row.get("name") or "").strip().lower()
    country = str(source_or_row.get("country") or source_or_row.get("region") or "").strip().lower()
    if name:
        return f"name:{country}|{name}"
    return f"path:{source_or_row.get('archived_pdf_path', '')}"


def _load_checkpoint(path: Path) -> dict[str, dict]:
    """Load already-processed guide rows keyed by guide id (JSONL; robust to a
    half-written last line from an interrupted run)."""
    done: dict[str, dict] = {}
    if not path.is_file():
        return done
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except Exception:
            continue  # skip a torn final line
        key = row.get("_guide_key") or _guide_key(row)
        done[key] = row
    return done


def run_guides(
    settings,
    logger,
    *,
    session: Any | None = None,
    limit: int | None = None,
    timeout: float = 30.0,
    workers: int = 4,
    resume: bool = True,
    discover_fao: bool = False,
    report: bool = False,
) -> dict:
    """Fetch + process every official guide; write the coded table and summary.

    Sources: the static country manifest by default, or — with
    ``discover_fao=True`` and an HTTP session — the FAO FBDG registry crawled
    *live* (every country + its actual downloadable guide files).

    Save & continue: each processed guide is appended to
    ``07_logs/guides_checkpoint.jsonl`` as it finishes, so an interrupted run
    resumes where it stopped (``resume=True``) without re-downloading or re-OCRing.
    Faster: guides are fetched + OCR'd concurrently in a thread pool (``workers``);
    tesseract runs as a subprocess so threads give real parallelism.

    Returns a summary dict (also written to ``07_logs/guides_summary.json``).
    """
    config_root = settings.config_root
    dest_dir = settings.output_dirs["03C_official_docs"]
    checkpoint_path = settings.output_dirs["07_logs"] / "guides_checkpoint.jsonl"
    if discover_fao and session is not None:
        from nutev.acquire.fao_discovery import discover_fao_guides

        sources = discover_fao_guides(session, timeout=timeout, limit=limit, workers=workers, logger=logger)
        logger.info("guias descobertos ao vivo (FAO)=%d", len(sources))
    else:
        sources = load_guide_sources(config_root)
        logger.info("guias no manifesto=%d", len(sources))

    if session is not None:
        # Live discovery already honored `limit` on the country list; the manifest
        # path still slices here.
        work_items = list(sources) if discover_fao else list(sources[: limit or len(sources)])
    else:
        # Offline: no fetch. Code any PDFs already archived in the official-docs
        # directory so the flow still produces output on a machine without net.
        logger.info("sem sessão HTTP — pulando download; processando PDFs já baixados")
        work_items = [
            {"name": p.stem, "archived_pdf_path": str(p), "source_url": "", "fulltext_status": "local_file"}
            for p in sorted(Path(dest_dir).glob("*")) if p.is_file()
        ]

    if not resume and checkpoint_path.is_file():
        # Fresh run: drop the old checkpoint so we don't append duplicates to it.
        checkpoint_path.unlink()
    done = _load_checkpoint(checkpoint_path) if resume else {}
    if done:
        logger.info("checkpoint: %d guias já processados — retomando", len(done))
    todo = [s for s in work_items if _guide_key(s) not in done]
    logger.info("guias a processar agora=%d (pulando %d já feitos)", len(todo), len(work_items) - len(todo))

    write_lock = threading.Lock()

    def _one(source: dict) -> dict:
        if session is not None:
            record = fetch_guide(source, dest_dir, session, timeout=timeout)
        else:
            record = dict(source)
        row = process_guide(record, settings, logger)
        row["_guide_key"] = _guide_key(source)
        # Append to the checkpoint the moment this guide is done, so progress
        # survives an interruption. Drop the big extracted_text from the record.
        line = json.dumps({k: v for k, v in row.items() if k != "extracted_text"}, ensure_ascii=False)
        with write_lock:
            with checkpoint_path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
        return row

    new_rows: list[dict] = []
    if todo:
        with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
            for row in pool.map(_one, todo):
                new_rows.append(row)

    # Union of previously-done rows and newly-processed ones, in manifest order.
    all_by_key = dict(done)
    for row in new_rows:
        all_by_key[row.get("_guide_key") or _guide_key(row)] = row
    rows = [all_by_key[_guide_key(s)] for s in work_items if _guide_key(s) in all_by_key]

    # Persist the coded table (flat CSV; the nested key_phrases stay in the JSON).
    table_rows = [{col: r.get(col, "") for col in _TABLE_COLUMNS} for r in rows]
    write_simple_csv(table_rows, settings.output_dirs["06_tables"] / "NUTEV_GUIDES_CODED.csv")

    # Tidy evidence table: one row per detected sub-theme snippet, each with its
    # verbatim evidence and the document's reference (a scoping-review goldmine).
    evidence: list[dict] = []
    for r in rows:
        evidence.extend(evidence_rows(r))
    write_simple_csv(evidence, settings.output_dirs["06_tables"] / "NUTEV_GUIDES_EVIDENCE.csv")

    # Reviewable domain-states table: one row per document × domain (A/B/C/D) with
    # the suggested state/intensity, the evidence snippet + page, and the
    # "machine_suggestion" marker — the queue two human reviewers work from.
    states: list[dict] = []
    for r in rows:
        states.extend(domain_state_rows(r))
    write_simple_csv(states, settings.output_dirs["06_tables"] / "NUTEV_GUIDES_DOMAIN_STATES.csv")

    # Entity registries (§7.1): file_asset × document_version × document_family +
    # the denominator registry — so files are never miscounted as documents.
    registries = build_registries(rows)
    logs = settings.output_dirs["07_logs"]
    write_simple_csv(registries["file_assets"], logs / "file_asset_registry.csv")
    write_simple_csv(registries["versions"], logs / "document_version_registry.csv")
    write_simple_csv(registries["families"], logs / "document_family_registry.csv")
    write_simple_csv(registries["denominators"], logs / "denominator_registry.csv")

    # Evidence Gems Bank (§14): rank the highest descriptive-value documents,
    # each tied to its snippet/page/reference and a suggested manuscript section.
    # Descriptive value only — NOT a quality / risk-of-bias score.
    gems = rank_gems(rows)
    write_simple_csv(gems, settings.output_dirs["06_tables"] / "NUTEV_GUIDES_EVIDENCE_GEMS.csv")
    (settings.output_dirs["10_curated"] / "best_gems.md").write_text(
        best_gems_markdown(gems), encoding="utf-8"
    )

    # Two-reviewer screening queue (§13): one item per document for two humans to
    # screen; docs with no usable text / poor OCR are flagged to a separate queue.
    # Nothing is export-ready until two reviewers validate (the export gate).
    queue = build_screening_queue(rows)
    write_simple_csv(queue, settings.output_dirs["06_tables"] / "NUTEV_GUIDES_SCREENING_QUEUE.csv")

    # Article-1 reproducible exports (§17): A/B/C/D matrix, PRISMA counts +
    # diagram, and the data dictionary. `included` stays pending (human review).
    from nutev.export.article1_exports import write_article1_exports

    exports = write_article1_exports(rows, registries, queue, settings)

    # Full per-guide detail (including the nested key phrases) as JSON.
    detail_path = settings.output_dirs["10_curated"] / "guides_coded.json"
    detail_path.parent.mkdir(parents=True, exist_ok=True)
    detail_path.write_text(
        json.dumps(
            [{k: v for k, v in r.items() if k != "extracted_text"} for r in rows],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    fetched = sum(1 for r in rows if r.get("fulltext_status") in {"fulltext_pdf", "fulltext_html", "local_file"})
    with_text = sum(1 for r in rows if r.get("extraction_status") in _FULLTEXT_OK)
    ocr_used = sum(1 for r in rows if r.get("used_ocr"))
    by_profile: dict[str, int] = {}
    for r in rows:
        prof = r.get("profile") or "none"
        by_profile[prof] = by_profile.get(prof, 0) + 1
    total_phrases = sum(int(r.get("n_key_phrases", 0) or 0) for r in rows)

    summary = {
        "source_mode": "fao_live_discovery" if discover_fao else "static_manifest",
        "guides_in_manifest": len(sources),
        "guides_processed": len(rows),
        "guides_new_this_run": len(new_rows),
        "guides_resumed_from_checkpoint": len(rows) - len(new_rows),
        "guides_fetched": fetched,
        "guides_with_fulltext": with_text,
        "guides_ocr_used": ocr_used,
        "key_phrases_total": total_phrases,
        "themes_detected_total": sum(int(r.get("n_themes", 0) or 0) for r in rows),
        "evidence_snippets_total": len(evidence),
        "file_assets": len(registries["file_assets"]),
        "document_versions": len(registries["versions"]),
        "document_families": len(registries["families"]),
        "evidence_gems": len(gems),
        "top_gem_score": gems[0]["gem_score"] if gems else 0,
        "screening_queue": len(queue),
        "screening_ready_to_screen": sum(1 for q in queue if q["screen_flag"] == "ready_to_screen"),
        "screening_no_full_text": sum(1 for q in queue if q["screen_flag"] != "ready_to_screen"),
        "abcd_matrix_rows": exports["abcd_matrix_rows"],
        "prisma_counts": exports["prisma_counts"],
        "profile_distribution": dict(sorted(by_profile.items())),
        "workers": workers,
        "checkpoint": str(checkpoint_path),
        "table_csv": str(settings.output_dirs["06_tables"] / "NUTEV_GUIDES_CODED.csv"),
        "detail_json": str(detail_path),
    }

    # Optional corpus report: fuzzy (content) dedup + thematic clustering + the
    # theme heatmap Excel. Degrades gracefully when scikit-learn/matplotlib are
    # not installed (see docs / the [report] extra). Never aborts a run.
    if report:
        try:
            from nutev.analysis.corpus_report import write_corpus_report

            summary["report"] = write_corpus_report(
                rows, settings.output_dirs["06_tables"], logger=logger
            )
        except Exception as exc:  # pragma: no cover - defensive
            summary["report"] = {"status": "error", "reason": str(exc)}

    (settings.output_dirs["07_logs"] / "guides_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary
