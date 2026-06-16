from __future__ import annotations

from nutev.querypacks import semantic_blocks
from nutev.querypacks.semantic_extensions import apply_semantic_extensions

CKM_RENAL_CARDIOMETABOLIC_TERMS = [
    "cardio-kidney-metabolic syndrome",
    "cardio kidney metabolic syndrome",
    "cardio-kidney-metabolic health",
    "cardio kidney metabolic health",
    "cardio-kidney-metabolic risk",
    "cardio kidney metabolic risk",
    "cardiorenal metabolic syndrome",
    "cardiorenal metabolic health",
    "cardiorenal metabolic risk",
]

CKM_RENAL_CARDIOMETABOLIC_DOCUMENT_TERMS = [
    "cardio-kidney-metabolic scientific statement",
    "cardio kidney metabolic scientific statement",
    "cardiorenal metabolic scientific statement",
    "cardio-kidney-metabolic consensus statement",
    "cardio kidney metabolic consensus statement",
    "cardio-kidney-metabolic clinical practice guideline",
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


def apply_querypack_extensions() -> None:
    apply_semantic_extensions()
    block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS["cardiometabolic_precision"]
    block["terms"] = _extend_unique(
        block.setdefault("terms", []),
        CKM_RENAL_CARDIOMETABOLIC_TERMS,
    )
    block["document_terms"] = _extend_unique(
        block.setdefault("document_terms", []),
        CKM_RENAL_CARDIOMETABOLIC_DOCUMENT_TERMS,
    )


apply_querypack_extensions()

__all__ = ["apply_querypack_extensions", "apply_semantic_extensions"]
