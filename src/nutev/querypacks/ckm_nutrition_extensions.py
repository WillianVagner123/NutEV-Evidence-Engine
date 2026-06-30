from __future__ import annotations

from nutev.querypacks import semantic_blocks

CKM_NUTRITION_TERMS = [
    "cardiovascular-kidney-metabolic nutrition",
    "cardiovascular kidney metabolic nutrition",
    "cardiovascular-kidney-metabolic dietary intervention",
    "cardiovascular kidney metabolic dietary intervention",
    "cardiovascular-kidney-metabolic lifestyle intervention",
    "cardiovascular kidney metabolic lifestyle intervention",
    "cardio-kidney-metabolic nutrition",
    "cardio kidney metabolic nutrition",
    "cardio-kidney-metabolic dietary intervention",
    "cardio kidney metabolic dietary intervention",
    "cardiorenal metabolic nutrition",
    "cardiorenal metabolic dietary intervention",
    "ckm nutrition",
    "ckm dietary intervention",
    "ckm lifestyle intervention",
    "ckm syndrome nutrition",
    "ckm syndrome dietary intervention",
]

CKM_NUTRITION_DOCUMENT_TERMS = [
    "cardiovascular-kidney-metabolic scientific statement",
    "cardiovascular kidney metabolic scientific statement",
    "cardiovascular-kidney-metabolic guideline",
    "cardiovascular kidney metabolic guideline",
    "cardiovascular-kidney-metabolic consensus",
    "cardiovascular kidney metabolic consensus",
    "cardiovascular-kidney-metabolic systematic review",
    "cardiovascular kidney metabolic systematic review",
    "cardio-kidney-metabolic guideline",
    "cardio kidney metabolic guideline",
    "ckm scientific statement",
    "ckm guideline",
    "ckm consensus",
    "ckm systematic review",
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


def apply_ckm_nutrition_extensions() -> None:
    for block_name in (
        "cardiometabolic_precision",
        "nutrition_care_delivery",
        "lifestyle_nutrition_patterns",
        "evidence_synthesis",
    ):
        _extend_semantic_block(
            block_name,
            terms=CKM_NUTRITION_TERMS,
            document_terms=CKM_NUTRITION_DOCUMENT_TERMS,
        )
