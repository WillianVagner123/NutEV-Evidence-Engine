from __future__ import annotations

from nutev.querypacks import semantic_blocks

CARDIOMETABOLIC_DIET_PATTERN_TERMS = [
    "mediterranean diet adherence",
    "mediterranean dietary adherence",
    "mediterranean diet intervention",
    "mediterranean dietary pattern intervention",
    "dash diet adherence",
    "dash dietary pattern adherence",
    "dash diet intervention",
    "dietary approaches to stop hypertension intervention",
    "mind diet adherence",
    "mind dietary pattern adherence",
    "mind diet intervention",
    "portfolio diet adherence",
    "portfolio dietary pattern",
    "portfolio diet intervention",
    "nordic diet adherence",
    "new nordic diet intervention",
    "healthy plant-based diet adherence",
    "healthy plant based diet adherence",
    "whole-food plant-based diet",
    "whole food plant based diet",
    "low glycemic index diet",
    "low glycaemic index diet",
    "low glycemic load diet",
    "low glycaemic load diet",
    "dietary portfolio",
    "dietary pattern adherence",
    "dietary pattern intervention",
    "healthy dietary pattern adherence",
    "cardiometabolic dietary pattern",
    "cardiometabolic diet quality",
]

CARDIOMETABOLIC_DIET_PATTERN_DOCUMENT_TERMS = [
    "mediterranean diet adherence intervention",
    "mediterranean diet intervention trial",
    "mediterranean diet systematic review",
    "dash diet adherence intervention",
    "dash diet intervention trial",
    "dash diet systematic review",
    "mind diet intervention trial",
    "portfolio diet intervention trial",
    "portfolio diet systematic review",
    "nordic diet intervention trial",
    "plant-based diet intervention trial",
    "plant based diet intervention trial",
    "low glycemic index diet trial",
    "low glycaemic index diet trial",
    "dietary pattern adherence intervention",
    "dietary pattern intervention trial",
    "cardiometabolic diet systematic review",
]

CARDIOMETABOLIC_DIET_BLOCKS = (
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


def apply_diet_pattern_precision_extensions() -> None:
    for block_name in CARDIOMETABOLIC_DIET_BLOCKS:
        _extend_semantic_block(
            block_name,
            terms=CARDIOMETABOLIC_DIET_PATTERN_TERMS,
            document_terms=CARDIOMETABOLIC_DIET_PATTERN_DOCUMENT_TERMS,
        )


apply_diet_pattern_precision_extensions()
