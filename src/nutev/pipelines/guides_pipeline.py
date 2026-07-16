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
from pathlib import Path
from typing import Any

from nutev.acquire.guias_fetcher import fetch_guides, load_guide_sources
from nutev.analysis.article1_coding import article1_record_fields
from nutev.analysis.keyphrases import keyphrase_fields
from nutev.export.metadata_tables import write_simple_csv
from nutev.extract.smart_extract import extract_document

_FULLTEXT_OK = {"ok", "ok_ocr", "fake_pdf_html", "fake_pdf_text"}

# Columns written to the coded-guides table (flat, human-readable).
_TABLE_COLUMNS = (
    "name", "country", "institution", "source_url", "access_date",
    "fulltext_status", "archived_pdf_path", "sha256", "archived_pdf_sha256",
    "aacods_authority_tier", "track", "extraction_status", "used_ocr", "chars",
    "profile", "n_domains", "domain_A", "domain_B", "domain_C", "domain_D",
    "n_key_phrases", "top_terms", "key_phrases_text",
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
    extraction: dict = {"extraction_status": "no_file", "used_ocr": False, "chars": 0, "text_path": ""}
    if pdf_path and Path(pdf_path).is_file():
        try:
            extraction = extract_document(
                Path(pdf_path),
                settings.output_dirs["04_ocr_text"],
                settings.output_dirs["05_extraction"],
                logger,
            )
        except Exception as exc:  # never abort the batch on one bad file
            logger.warning("extract falhou guia=%s erro=%s", pdf_path, exc)
            extraction = {"extraction_status": "failed", "used_ocr": False, "chars": 0, "text_path": ""}

    row["extraction_status"] = extraction.get("extraction_status", "")
    row["used_ocr"] = bool(extraction.get("used_ocr", False))
    row["chars"] = int(extraction.get("chars", 0) or 0)
    row["extracted_text"] = _extracted_text_for(extraction)

    # A/B/C/D coding + provenance/AACODS (assistive; enters human review).
    row.update(article1_record_fields(row))
    # Key phrases / key sentences per domain + top terms.
    row.update(keyphrase_fields(row))
    return row


def run_guides(
    settings,
    logger,
    *,
    session: Any | None = None,
    limit: int | None = None,
    timeout: float = 30.0,
) -> dict:
    """Fetch + process every official guide; write the coded table and summary.

    Returns a summary dict (also written to ``07_logs/guides_summary.json``).
    """
    config_root = settings.config_root
    dest_dir = settings.output_dirs["03C_official_docs"]
    sources = load_guide_sources(config_root)
    logger.info("guias no manifesto=%d", len(sources))

    if session is not None:
        records = fetch_guides(sources, dest_dir, session, timeout=timeout, limit=limit)
        logger.info("guias baixados (tentativa)=%d", len(records))
    else:
        # Offline: no fetch. Code any PDFs already archived in the official-docs
        # directory so the flow still produces output on a machine without net.
        logger.info("sem sessão HTTP — pulando download; processando PDFs já baixados")
        records = [
            {"name": p.stem, "archived_pdf_path": str(p), "source_url": "", "fulltext_status": "local_file"}
            for p in sorted(Path(dest_dir).glob("*")) if p.is_file()
        ]

    rows = [process_guide(rec, settings, logger) for rec in records]

    # Persist the coded table (flat CSV; the nested key_phrases stay in the JSON).
    table_rows = [{col: r.get(col, "") for col in _TABLE_COLUMNS} for r in rows]
    write_simple_csv(table_rows, settings.output_dirs["06_tables"] / "NUTEV_GUIDES_CODED.csv")

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
        "guides_in_manifest": len(sources),
        "guides_processed": len(rows),
        "guides_fetched": fetched,
        "guides_with_fulltext": with_text,
        "guides_ocr_used": ocr_used,
        "key_phrases_total": total_phrases,
        "profile_distribution": dict(sorted(by_profile.items())),
        "table_csv": str(settings.output_dirs["06_tables"] / "NUTEV_GUIDES_CODED.csv"),
        "detail_json": str(detail_path),
    }
    (settings.output_dirs["07_logs"] / "guides_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary
