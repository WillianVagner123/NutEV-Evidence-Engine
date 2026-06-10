from __future__ import annotations

from nutev.querypacks import semantic_blocks

CKM_ADDITIONAL_TERMS = [
    "cardiovascular-kidney-metabolic",
    "cardiovascular kidney metabolic",
    "cardiovascular-kidney-metabolic disease",
    "cardiovascular kidney metabolic disease",
    "cardio-kidney-metabolic syndrome",
    "cardio kidney metabolic syndrome",
    "cardio-kidney-metabolic health",
    "cardio kidney metabolic health",
    "cardio-kidney-metabolic risk",
    "cardio kidney metabolic risk",
    "ckm disease",
    "ckm health framework",
    "ckm risk framework",
]

CKM_ADDITIONAL_DOCUMENT_TERMS = [
    "aha presidential advisory",
    "american heart association presidential advisory",
    "cardiovascular-kidney-metabolic presidential advisory",
    "cardiovascular kidney metabolic presidential advisory",
    "ckm presidential advisory",
    "ckm health advisory",
    "ckm health framework",
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


def apply_ckm_term_extensions() -> None:
    block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS.setdefault(
        "cardiometabolic_precision",
        {"terms": [], "document_terms": []},
    )
    block["terms"] = _extend_unique(block.setdefault("terms", []), CKM_ADDITIONAL_TERMS)
    block["document_terms"] = _extend_unique(
        block.setdefault("document_terms", []),
        CKM_ADDITIONAL_DOCUMENT_TERMS,
    )
