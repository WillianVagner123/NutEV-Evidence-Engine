from __future__ import annotations

from nutev.querypacks import semantic_blocks

CARDIOMETABOLIC_DIET_ADHERENCE_TERMS = [
    "dietary pattern adherence",
    "diet pattern adherence",
    "healthy diet adherence",
    "healthy eating pattern adherence",
    "mediterranean diet adherence",
    "mediterranean dietary pattern adherence",
    "dash diet adherence",
    "dietary approaches to stop hypertension adherence",
    "plant-based diet adherence",
    "plant based diet adherence",
    "healthy plant-based diet adherence",
    "healthy plant based diet adherence",
    "vegetarian diet adherence",
    "vegan diet adherence",
    "portfolio diet adherence",
    "nordic diet adherence",
    "planetary health diet adherence",
    "eat-lancet diet adherence",
    "low-carbohydrate diet adherence",
    "low carbohydrate diet adherence",
    "carbohydrate-restricted diet adherence",
    "carbohydrate restricted diet adherence",
    "ketogenic diet adherence",
    "time-restricted eating adherence",
    "intermittent fasting adherence",
    "dietary adherence score",
    "dietary adherence index",
    "diet adherence score",
    "diet adherence index",
    "diet quality adherence",
    "nutrition intervention adherence",
]

CARDIOMETABOLIC_DIET_ADHERENCE_DOCUMENT_TERMS = [
    "dietary pattern adherence score",
    "dietary pattern adherence index",
    "diet adherence score validation",
    "diet adherence index validation",
    "dietary adherence score validation",
    "dietary adherence index validation",
    "mediterranean diet adherence score",
    "mediterranean diet adherence index",
    "dash diet adherence score",
    "dash diet adherence index",
    "plant-based diet adherence score",
    "plant based diet adherence score",
    "healthy plant-based diet adherence index",
    "healthy plant based diet adherence index",
    "portfolio diet adherence score",
    "nordic diet adherence score",
    "planetary health diet adherence score",
    "low-carbohydrate diet adherence score",
    "low carbohydrate diet adherence score",
    "time-restricted eating adherence trial",
    "intermittent fasting adherence trial",
    "nutrition intervention adherence study",
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


def apply_diet_adherence_pattern_extensions() -> None:
    for block_name in (
        "adherence_persistence",
        "lifestyle_nutrition_patterns",
        "cardiometabolic_precision",
    ):
        _extend_semantic_block(
            block_name,
            terms=CARDIOMETABOLIC_DIET_ADHERENCE_TERMS,
            document_terms=CARDIOMETABOLIC_DIET_ADHERENCE_DOCUMENT_TERMS,
        )


apply_diet_adherence_pattern_extensions()
