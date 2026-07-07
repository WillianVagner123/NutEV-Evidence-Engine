from __future__ import annotations

from nutev.querypacks import semantic_blocks

CARDIORENAL_METABOLIC_TERMS = [
    "cardiorenal metabolic syndrome",
    "cardio-renal-metabolic syndrome",
    "cardiorenal-metabolic syndrome",
    "cardiorenal metabolic health",
    "cardiorenal metabolic risk",
    "cardiorenal metabolic nutrition",
    "cardio-renal-metabolic nutrition",
    "cardiorenal metabolic dietary intervention",
    "cardiorenal metabolic lifestyle intervention",
    "cardiorenal metabolic nutrition intervention",
]

CARDIORENAL_METABOLIC_DOCUMENT_TERMS = [
    "cardiorenal metabolic syndrome guideline",
    "cardiorenal metabolic syndrome consensus",
    "cardiorenal metabolic syndrome scientific statement",
    "cardiorenal metabolic syndrome systematic review",
    "cardiorenal metabolic nutrition intervention trial",
    "cardiorenal metabolic dietary intervention trial",
    "cardiorenal metabolic lifestyle intervention trial",
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


def apply_cardiorenal_extensions() -> None:
    for block_name in (
        "cardiometabolic_precision",
        "lifestyle_nutrition_patterns",
        "implementation_science",
    ):
        _extend_semantic_block(
            block_name,
            terms=CARDIORENAL_METABOLIC_TERMS,
            document_terms=CARDIORENAL_METABOLIC_DOCUMENT_TERMS,
        )


apply_cardiorenal_extensions()
