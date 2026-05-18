from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from nutev.engine.identity import (
    as_text,
    compute_document_key,
    has_full_text,
    normalize_for_match,
)

PRISMA_COLUMNS = [
    "registros_identificados",
    "duplicados_removidos",
    "registros_triados",
    "documentos_com_pdf_ou_html",
    "documentos_metadata_only",
    "documentos_priorizados",
]

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


def _compute_document_key(row: dict) -> str:
    return compute_document_key(row)[0]


def _has_full_text(row: dict) -> bool:
    return has_full_text(row)


def _is_prioritized(row: dict) -> bool:
    try:
        score = float(row.get("relevance_score") or row.get("score") or 0)
    except Exception:
        score = 0.0
    text = " ".join(
        [
            as_text(row.get("title")),
            as_text(row.get("evidence_type")),
            as_text(row.get("domains")),
            as_text(row.get("outcomes")),
            as_text(row.get("diet_patterns")),
            as_text(row.get("clinical_conditions")),
            as_text(row.get("main_terms")),
        ]
    )
    normalized_text = normalize_for_match(text)
    return score >= 8 and any(
        normalize_for_match(term) in normalized_text for term in _PRIORITY_TERMS
    )


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
        "documentos_com_pdf_ou_html": sum(
            1 for row in unique_rows if _has_full_text(row)
        ),
        "documentos_metadata_only": sum(
            1 for row in unique_rows if not _has_full_text(row)
        ),
        "documentos_priorizados": sum(
            1 for row in unique_rows if _is_prioritized(row)
        ),
    }


def export_prisma(flow: dict, xlsx: Path, json_path: Path) -> None:
    xlsx.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([flow], columns=PRISMA_COLUMNS).to_excel(xlsx, index=False)
    json_path.write_text(
        json.dumps(flow, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
