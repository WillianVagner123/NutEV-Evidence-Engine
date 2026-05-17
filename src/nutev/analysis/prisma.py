from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import pandas as pd

from nutev.engine.validators import normalize_doi

FULL_TEXT_EXTRACTION_STATUSES = {
    "ok",
    "ok_ocr",
    "ok_native_low_confidence",
    "fake_pdf_html",
    "fake_pdf_text",
}


def _normalize_url(value: str | None) -> str:
    if not value:
        return ""
    parsed = urlparse(str(value).strip())
    return urlunparse(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip("/"),
            "",
            parsed.query,
            "",
        )
    )


def _normalize_title(value: str | None) -> str:
    title = " ".join((value or "").lower().split())
    return "".join(char for char in title if char.isalnum() or char.isspace()).strip()


def _row_hash(row: dict) -> str:
    payload = json.dumps(row, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _document_key(row: dict) -> str:
    doi = normalize_doi(row.get("doi"))
    if doi:
        return f"doi:{doi}"

    pmid = str(row.get("pmid") or "").strip().lower()
    if pmid:
        return f"pmid:{pmid}"

    pmcid = str(row.get("pmcid") or "").strip().lower()
    if pmcid:
        return f"pmcid:{pmcid}"

    canonical_url = _normalize_url(
        row.get("final_url")
        or row.get("resolved_url")
        or row.get("canonical_url")
        or row.get("url")
        or row.get("original_url")
    )
    if canonical_url:
        return f"url:{canonical_url}"

    normalized_title = _normalize_title(row.get("title"))
    year = str(row.get("year") or "").strip()
    if normalized_title:
        return f"title_year:{normalized_title}|{year}"

    return f"rowhash:{_row_hash(row)}"


def _as_float(value: object) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _domains_present(row: dict) -> bool:
    domains = str(row.get("domains") or "").strip()
    nutev_objects = str(row.get("nutev_objects") or "").strip()
    return bool(domains or nutev_objects)


def _has_full_text(row: dict) -> bool:
    extraction_status = str(row.get("extraction_status") or "")
    if extraction_status in FULL_TEXT_EXTRACTION_STATUSES:
        return True
    return bool(str(row.get("file_path") or row.get("artifact_path") or "").strip())


def build_prisma_flow(all_rows: list[dict], download_manifest: list[dict], extraction_manifest: list[dict]) -> dict:
    identified = len(all_rows)
    grouped: dict[str, list[dict]] = {}
    for row in all_rows:
        grouped.setdefault(_document_key(row), []).append(row)

    unique_documents = list(grouped.values())
    triaged = len(unique_documents)
    duplicates_removed = max(0, identified - triaged)

    documents_with_full_text = sum(1 for group in unique_documents if any(_has_full_text(row) for row in group))
    documents_metadata_only = max(0, triaged - documents_with_full_text)
    documents_prioritized = sum(
        1
        for group in unique_documents
        if any(_domains_present(row) and _as_float(row.get("score") or row.get("relevance_score")) >= 8 for row in group)
    )
    docs_analyzed = sum(1 for group in unique_documents if any(_domains_present(row) for row in group))
    docs_texto_extraido = sum(
        1
        for group in unique_documents
        if any(str(row.get("extraction_status") or "") in FULL_TEXT_EXTRACTION_STATUSES for row in group)
    )

    cls = lambda key: sum(1 for row in all_rows if key in str(row.get("nutev_objects") or ""))
    return {
        "registros_identificados": identified,
        "duplicados_removidos": duplicates_removed,
        "registros_triados": triaged,
        "registros_excluidos": max(0, triaged - len(download_manifest)),
        "documentos_com_pdf_ou_html": documents_with_full_text,
        "documentos_metadata_only": documents_metadata_only,
        "documentos_priorizados": documents_prioritized,
        "docs_texto_extraido": docs_texto_extraido,
        "docs_analisados": docs_analyzed,
        "docs_priorizados": documents_prioritized,
        "class_evidence_table": cls("evidence_table"),
        "class_protocol_rule": cls("protocol_rule"),
        "class_questionnaire_item_candidate": cls("questionnaire_item_candidate"),
        "class_framework_component": cls("framework_component"),
        "download_manifest_rows": len(download_manifest),
        "extraction_manifest_rows": len(extraction_manifest),
    }


def export_prisma(flow: dict, xlsx: Path, json_path: Path) -> None:
    xlsx.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([flow]).to_excel(xlsx, index=False)
    json_path.write_text(json.dumps(flow, indent=2, ensure_ascii=False), encoding="utf-8")
