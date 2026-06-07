from __future__ import annotations

from nutev.querypacks import semantic_blocks

CARDIOPROTECTIVE_DIET_PATTERN_TERMS = [
    "portfolio dietary pattern",
    "dietary portfolio",
    "portfolio diet adherence",
    "portfolio diet score",
    "cholesterol-lowering dietary pattern",
    "cholesterol lowering dietary pattern",
    "plant sterol dietary portfolio",
    "viscous fiber dietary portfolio",
    "new nordic diet adherence",
    "healthy nordic diet",
    "healthy nordic dietary pattern",
    "nordic dietary pattern",
    "baltic sea diet",
    "plant-based diet index",
    "plant based diet index",
    "healthy plant-based diet index",
    "healthy plant based diet index",
    "unhealthy plant-based diet index",
    "unhealthy plant based diet index",
    "plant-based dietary index",
    "plant based dietary index",
    "provegetarian dietary pattern",
    "pro-vegetarian dietary pattern",
    "flexitarian diet",
    "semi-vegetarian diet",
    "planetary health diet index",
    "eat-lancet diet score",
    "eat-lancet reference diet",
    "sustainable healthy diet index",
    "healthy sustainable dietary pattern",
]

CARDIOPROTECTIVE_DIET_PATTERN_DOCUMENT_TERMS = [
    "portfolio diet systematic review",
    "portfolio diet meta-analysis",
    "portfolio diet clinical trial",
    "portfolio diet randomized trial",
    "portfolio diet guideline",
    "portfolio diet consensus",
    "nordic diet systematic review",
    "nordic diet meta-analysis",
    "new nordic diet clinical trial",
    "plant-based diet index validation",
    "plant based diet index validation",
    "plant-based diet systematic review",
    "plant based diet systematic review",
    "planetary health diet systematic review",
    "eat-lancet diet score validation",
    "sustainable healthy diet guideline",
    "sustainable healthy diet systematic review",
]

CARDIOMETABOLIC_DIET_PATTERN_TERMS = [
    "dietary portfolio",
    "portfolio diet",
    "portfolio dietary pattern",
    "cholesterol-lowering dietary pattern",
    "plant sterol dietary portfolio",
    "viscous fiber dietary portfolio",
    "healthy nordic diet",
    "nordic dietary pattern",
    "plant-based diet index",
    "healthy plant-based diet index",
    "planetary health diet index",
    "eat-lancet diet score",
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
    terms: list[str] | None = None,
    document_terms: list[str] | None = None,
) -> None:
    block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS.setdefault(
        block_name,
        {"terms": [], "document_terms": []},
    )
    if terms:
        block["terms"] = _extend_unique(block.setdefault("terms", []), terms)
    if document_terms:
        block["document_terms"] = _extend_unique(
            block.setdefault("document_terms", []),
            document_terms,
        )


def apply_diet_pattern_extensions() -> None:
    _extend_semantic_block(
        "lifestyle_nutrition_patterns",
        terms=CARDIOPROTECTIVE_DIET_PATTERN_TERMS,
        document_terms=CARDIOPROTECTIVE_DIET_PATTERN_DOCUMENT_TERMS,
    )
    _extend_semantic_block(
        "cardiometabolic_precision",
        terms=CARDIOMETABOLIC_DIET_PATTERN_TERMS,
    )
