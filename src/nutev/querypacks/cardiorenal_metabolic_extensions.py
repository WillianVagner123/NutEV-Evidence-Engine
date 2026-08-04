from __future__ import annotations

from nutev.querypacks import semantic_blocks

CARDIORENAL_METABOLIC_TERMS = [
    "cardiorenal metabolic syndrome",
    "cardio-renal-metabolic syndrome",
    "cardiorenal-metabolic syndrome",
    "cardiorenal metabolic health",
    "cardiorenal metabolic risk",
    "cardiorenal-metabolic health",
    "cardiorenal-metabolic risk",
]

CARDIORENAL_METABOLIC_DOCUMENT_TERMS = [
    "cardiorenal metabolic syndrome guideline",
    "cardiorenal metabolic syndrome consensus",
    "cardiorenal metabolic syndrome scientific statement",
    "cardiorenal metabolic syndrome practice guidance",
    "cardiorenal metabolic syndrome lifestyle intervention",
    "cardiorenal metabolic syndrome nutrition intervention",
    "cardiorenal metabolic syndrome dietary intervention",
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


def apply_cardiorenal_metabolic_extensions() -> None:
    block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS.setdefault(
        "cardiometabolic_precision",
        {"terms": [], "document_terms": []},
    )
    block["terms"] = _extend_unique(
        block.setdefault("terms", []),
        CARDIORENAL_METABOLIC_TERMS,
    )
    block["document_terms"] = _extend_unique(
        block.setdefault("document_terms", []),
        CARDIORENAL_METABOLIC_DOCUMENT_TERMS,
    )
