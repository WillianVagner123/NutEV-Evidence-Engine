from __future__ import annotations

from nutev.querypacks import semantic_blocks

CKM_NUTRITION_TERMS = [
    "cardiovascular-kidney-metabolic syndrome",
    "cardiovascular kidney metabolic syndrome",
    "cardiovascular-kidney-metabolic disease",
    "cardiovascular kidney metabolic disease",
    "cardiovascular-kidney-metabolic health",
    "cardiovascular kidney metabolic health",
    "cardiovascular-kidney-metabolic risk",
    "cardiovascular kidney metabolic risk",
    "cardiovascular-kidney-metabolic stage",
    "cardiovascular kidney metabolic stage",
    "cardiovascular-kidney-metabolic staging",
    "cardiovascular kidney metabolic staging",
    "ckm syndrome",
    "ckm disease",
    "ckm health",
    "ckm risk",
    "ckm stage",
    "ckm staging",
    "ckm nutrition therapy",
    "ckm dietary intervention",
    "ckm lifestyle intervention",
    "cardiovascular-kidney-metabolic nutrition therapy",
    "cardiovascular kidney metabolic nutrition therapy",
    "cardiovascular-kidney-metabolic dietary intervention",
    "cardiovascular kidney metabolic dietary intervention",
    "cardiovascular-kidney-metabolic lifestyle intervention",
    "cardiovascular kidney metabolic lifestyle intervention",
]

CKM_DOCUMENT_TERMS = [
    "cardiovascular-kidney-metabolic scientific statement",
    "cardiovascular kidney metabolic scientific statement",
    "cardiovascular-kidney-metabolic presidential advisory",
    "cardiovascular kidney metabolic presidential advisory",
    "cardiovascular-kidney-metabolic clinical practice guideline",
    "cardiovascular kidney metabolic clinical practice guideline",
    "cardiovascular-kidney-metabolic consensus statement",
    "cardiovascular kidney metabolic consensus statement",
    "cardiovascular-kidney-metabolic clinical decision pathway",
    "cardiovascular kidney metabolic clinical decision pathway",
    "cardiovascular-kidney-metabolic systematic review",
    "cardiovascular kidney metabolic systematic review",
    "ckm scientific statement",
    "ckm presidential advisory",
    "ckm clinical practice guideline",
    "ckm consensus statement",
    "ckm clinical decision pathway",
    "ckm systematic review",
]

CKM_TARGET_BLOCKS = (
    "cardiometabolic_precision",
    "lifestyle_nutrition_patterns",
    "nutrition_care_delivery",
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
    for block_name in CKM_TARGET_BLOCKS:
        _extend_semantic_block(
            block_name,
            terms=CKM_NUTRITION_TERMS,
            document_terms=CKM_DOCUMENT_TERMS,
        )
