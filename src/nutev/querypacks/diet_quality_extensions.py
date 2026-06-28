from __future__ import annotations

from nutev.querypacks import semantic_blocks

DIET_QUALITY_INDEX_VARIANT_TERMS = [
    "hei-2015",
    "healthy eating index 2015",
    "hei 2015",
    "ahei-2010",
    "alternate healthy eating index 2010",
    "ahei 2010",
    "diet quality index international",
    "diet quality index-international",
    "dqi-i",
    "mediterranean diet adherence score",
    "alternate mediterranean diet score",
    "alternative mediterranean diet score",
    "aMED score",
    "mMED score",
    "dash diet adherence score",
    "dash adherence score",
    "plant-based diet score",
    "healthful plant-based diet index",
    "healthful plant based diet index",
    "unhealthful plant-based diet index",
    "unhealthful plant based diet index",
    "healthy eating score",
    "healthy diet score",
]

DIET_QUALITY_INDEX_VARIANT_DOCUMENT_TERMS = [
    "healthy eating index 2015 validation",
    "alternate healthy eating index 2010 validation",
    "diet quality index international validation",
    "mediterranean diet adherence score validation",
    "dash diet adherence score validation",
    "plant-based diet score validation",
    "healthful plant-based diet index validation",
    "diet quality index validation",
]

DIET_QUALITY_TARGET_BLOCKS = (
    "adherence_persistence",
    "cardiometabolic_precision",
    "lifestyle_nutrition_patterns",
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


def apply_diet_quality_index_extensions() -> None:
    for block_name in DIET_QUALITY_TARGET_BLOCKS:
        _extend_semantic_block(
            block_name,
            terms=DIET_QUALITY_INDEX_VARIANT_TERMS,
            document_terms=DIET_QUALITY_INDEX_VARIANT_DOCUMENT_TERMS,
        )
