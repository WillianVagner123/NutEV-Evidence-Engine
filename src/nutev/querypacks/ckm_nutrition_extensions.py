from __future__ import annotations

from nutev.querypacks import semantic_blocks

CKM_NUTRITION_TERMS = [
    "cardiovascular-kidney-metabolic nutrition",
    "cardiovascular kidney metabolic nutrition",
    "cardiovascular-kidney-metabolic diet",
    "cardiovascular kidney metabolic diet",
    "cardiovascular-kidney-metabolic dietary intervention",
    "cardiovascular kidney metabolic dietary intervention",
    "cardiovascular-kidney-metabolic lifestyle intervention",
    "cardiovascular kidney metabolic lifestyle intervention",
    "cardiovascular-kidney-metabolic nutrition therapy",
    "cardiovascular kidney metabolic nutrition therapy",
    "ckm nutrition",
    "ckm diet",
    "ckm dietary intervention",
    "ckm lifestyle intervention",
    "ckm nutrition therapy",
    "ckm syndrome nutrition",
    "ckm syndrome diet",
    "ckm syndrome dietary intervention",
    "ckm syndrome lifestyle intervention",
    "ckm syndrome nutrition therapy",
]

CKM_NUTRITION_DOCUMENT_TERMS = [
    "cardiovascular-kidney-metabolic nutrition guideline",
    "cardiovascular kidney metabolic nutrition guideline",
    "cardiovascular-kidney-metabolic dietary guideline",
    "cardiovascular kidney metabolic dietary guideline",
    "cardiovascular-kidney-metabolic lifestyle guideline",
    "cardiovascular kidney metabolic lifestyle guideline",
    "cardiovascular-kidney-metabolic scientific statement",
    "cardiovascular kidney metabolic scientific statement",
    "cardiovascular-kidney-metabolic consensus statement",
    "cardiovascular kidney metabolic consensus statement",
    "ckm nutrition guideline",
    "ckm dietary guideline",
    "ckm lifestyle guideline",
    "ckm scientific statement",
    "ckm consensus statement",
    "ckm syndrome nutrition guideline",
    "ckm syndrome dietary guideline",
    "ckm syndrome lifestyle guideline",
    "ckm syndrome systematic review",
]

_TARGET_BLOCKS = (
    "cardiometabolic_precision",
    "lifestyle_nutrition_patterns",
    "nutrition_care_delivery",
    "evidence_synthesis",
)


def _extend_unique(existing: list[str], additions: list[str]) -> list[str]:
    seen = {item.lower() for item in existing}
    for item in additions:
        value = item.strip()
        if not value or value.lower() in seen:
            continue
        existing.append(value)
        seen.add(value.lower())
    return existing


def apply_ckm_nutrition_extensions() -> None:
    for block_name in _TARGET_BLOCKS:
        block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS.setdefault(
            block_name,
            {"terms": [], "document_terms": []},
        )
        block["terms"] = _extend_unique(
            block.setdefault("terms", []),
            CKM_NUTRITION_TERMS,
        )
        block["document_terms"] = _extend_unique(
            block.setdefault("document_terms", []),
            CKM_NUTRITION_DOCUMENT_TERMS,
        )


apply_ckm_nutrition_extensions()
