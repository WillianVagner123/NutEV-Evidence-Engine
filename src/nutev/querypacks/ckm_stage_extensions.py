from __future__ import annotations

from nutev.querypacks import semantic_blocks

CKM_STAGE_RISK_TERMS = [
    "cardiovascular-kidney-metabolic staging",
    "cardiovascular kidney metabolic staging",
    "ckm staging",
    "ckm stage",
    "ckm stages",
    "ckm risk stage",
    "ckm risk stages",
    "ckm risk prediction",
    "ckm risk assessment",
    "ckm health stages",
    "cardiovascular-kidney-metabolic risk prediction",
    "cardiovascular kidney metabolic risk prediction",
    "cardiovascular-kidney-metabolic risk assessment",
    "cardiovascular kidney metabolic risk assessment",
    "prevent risk equations",
    "prevent equations",
    "aha prevent risk",
    "aha prevent equations",
    "kidney-metabolic risk",
    "kidney metabolic risk",
]

CKM_STAGE_RISK_DOCUMENT_TERMS = [
    "ckm scientific statement",
    "ckm presidential advisory",
    "ckm risk prediction statement",
    "ckm staging statement",
    "cardiovascular-kidney-metabolic scientific statement",
    "cardiovascular kidney metabolic scientific statement",
    "cardiovascular-kidney-metabolic presidential advisory",
    "cardiovascular kidney metabolic presidential advisory",
    "prevent risk equations scientific statement",
    "prevent equations scientific statement",
    "cardiovascular-kidney-metabolic systematic review",
    "cardiovascular kidney metabolic systematic review",
]


def _extend_unique(existing: list[str], additions: list[str]) -> list[str]:
    seen = {item.lower() for item in existing}
    for item in additions:
        value = item.strip()
        if not value or value.lower() in seen:
            continue
        existing.append(value)
        seen.add(value.lower())
    return existing


def _extend_semantic_block(
    block_name: str,
    *,
    terms: list[str],
    document_terms: list[str],
) -> None:
    block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS.setdefault(
        block_name,
        {"terms": [], "document_terms": []},
    )
    block["terms"] = _extend_unique(block.setdefault("terms", []), terms)
    block["document_terms"] = _extend_unique(
        block.setdefault("document_terms", []),
        document_terms,
    )


def apply_ckm_stage_extensions() -> None:
    _extend_semantic_block(
        "cardiometabolic_precision",
        terms=CKM_STAGE_RISK_TERMS,
        document_terms=CKM_STAGE_RISK_DOCUMENT_TERMS,
    )
    _extend_semantic_block(
        "evidence_synthesis",
        terms=CKM_STAGE_RISK_TERMS,
        document_terms=CKM_STAGE_RISK_DOCUMENT_TERMS,
    )
