from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import pandas as pd

PRISMA_COLUMNS = [
    "registros_identificados",
    "duplicados_removidos",
    "registros_triados",
    "documentos_com_pdf_ou_html",
    "documentos_metadata_only",
    "documentos_priorizados",
]

_WHITESPACE_RE = re.compile(r"\s+")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
_PRIORITY_TERMS = [
    "obesity",
    "obesidade",
    "overweight",
    "sobrepeso",
    "cardiometabolic",
    "cardiometabolic risk",
    "diabetes",
    "type 2 diabetes",
    "hypertension",
    "hipertensao",
    "hipertensão",
    "dyslipidemia",
    "dislipidemia",
    "masld",
    "nafld",
    "mediterranean",
    "dash",
    "mind",
    "plant-based",
    "plant based",
    "eat-lancet",
    "planetary health diet",
    "dietary guideline",
    "dietary guidelines",
    "food-based dietary guideline",
    "food-based dietary guidelines",
    "lifestyle medicine",
    "medicina do estilo de vida",
    "culinary medicine",
    "food literacy",
    "literacia alimentar",
    "adherence",
    "adesao",
    "adesão",
    "implementation",
    "implementacao",
    "implementação",
    "barrier",
    "barriers",
    "facilitator",
    "facilitators",
    "commensality",
    "comensalidade",
    "meal planning",
    "behavior change",
    "behaviour change",
    "self-efficacy",
]


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
        return text.strip().rstrip("/").lower()
    path = parsed.path.rstrip("/") or "/"
    normalized = urlunsplit(
        (parsed.scheme.lower(), parsed.netloc.lower(), path, "", "")
    )
    return normalized.rstrip("/")


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


def _compute_document_key(row: dict) -> str:
    doi = _normalize_doi(row.get("doi"))
    if doi:
        return doi

    pmid = _as_text(row.get("pmid"))
    if pmid:
        return f"pmid:{pmid}"

    pmcid = _as_text(row.get("pmcid")).lower()
    if pmcid:
        return f"pmcid:{pmcid}"

    url = _normalize_url(
        row.get("final_url") or row.get("original_url") or row.get("resolved_url") or row.get("url")
    )
    if url:
        return url

    title = _normalize_title(row.get("title"))
    year = _normalize_year(row.get("year"))
    if title and year:
        return f"{title}::{year}"

    return _hash_fallback(row)


def _has_full_text(row: dict) -> bool:
    statuses = {
        _as_text(row.get("download_status")).lower(),
        _as_text(row.get("capture_status")).lower(),
        _as_text(row.get("extraction_status")).lower(),
    }
    if "pdf" in statuses or "html_snapshot" in statuses or "ok" in statuses:
        return True
    return bool(_as_text(row.get("file_path")) or _as_text(row.get("text_path")))


def _is_prioritized(row: dict) -> bool:
    try:
        score = float(row.get("relevance_score") or row.get("score") or 0)
    except Exception:
        score = 0.0
    text = " ".join(
        [
            _as_text(row.get("title")),
            _as_text(row.get("evidence_type")),
            _as_text(row.get("domains")),
            _as_text(row.get("outcomes")),
            _as_text(row.get("diet_patterns")),
            _as_text(row.get("clinical_conditions")),
            _as_text(row.get("main_terms")),
        ]
    ).lower()
    return score >= 8 and any(term in text for term in _PRIORITY_TERMS)


def build_prisma_flow(
    all_rows: list[dict],
    download_manifest: list[dict],
    extraction_manifest: list[dict],
) -> dict:
    del download_manifest, extraction_manifest
    identified = len(all_rows)
    unique_documents: dict[str, dict] = {}
    for row in all_rows:
        key = _compute_document_key(row)
        chosen = unique_documents.get(key)
        if chosen is None:
            unique_documents[key] = row
            continue
        if _has_full_text(row) and not _has_full_text(chosen):
            unique_documents[key] = row
            continue
        if _is_prioritized(row) and not _is_prioritized(chosen):
            unique_documents[key] = row
            continue

    unique_rows = list(unique_documents.values())
    triaged = len(unique_rows)
    return {
        "registros_identificados": identified,
        "duplicados_removidos": max(0, identified - triaged),
        "registros_triados": triaged,
        "documentos_com_pdf_ou_html": sum(1 for row in unique_rows if _has_full_text(row)),
        "documentos_metadata_only": sum(1 for row in unique_rows if not _has_full_text(row)),
        "documentos_priorizados": sum(1 for row in unique_rows if _is_prioritized(row)),
    }


def export_prisma(flow: dict, xlsx: Path, json_path: Path) -> None:
    xlsx.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([flow], columns=PRISMA_COLUMNS).to_excel(xlsx, index=False)
    json_path.write_text(
        json.dumps(flow, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
