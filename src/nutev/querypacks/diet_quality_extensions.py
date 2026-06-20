from __future__ import annotations

from nutev.querypacks import semantic_blocks

CARDIOMETABOLIC_DIET_QUALITY_TERMS = [
    "dietary fiber",
    "dietary fibre",
    "fiber intake",
    "fibre intake",
    "high-fiber diet",
    "high fiber diet",
    "high-fibre diet",
    "high fibre diet",
    "whole grain",
    "whole grains",
    "whole-grain diet",
    "whole grain diet",
    "wholegrain diet",
    "legume intake",
    "legume consumption",
    "pulses intake",
    "nut intake",
    "nut consumption",
    "low glycemic index diet",
    "low-glycemic-index diet",
    "low glycaemic index diet",
    "low-glycaemic-index diet",
    "glycemic index diet",
    "glycaemic index diet",
    "dietary carbohydrate quality",
    "carbohydrate quality",
    "protein quality",
    "plant protein",
    "plant-based protein",
    "plant based protein",
    "healthy eating plan",
    "healthy eating pattern",
    "DASH eating plan",
    "DASH dietary pattern",
    "Mediterranean eating pattern",
    "Mediterranean-style diet",
    "Mediterranean style diet",
    "MIND eating pattern",
    "MIND dietary pattern",
    "portfolio dietary pattern",
    "dietary portfolio",
    "cardioprotective diet",
    "cardioprotective dietary pattern",
]

CARDIOMETABOLIC_DIET_QUALITY_DOCUMENT_TERMS = [
    "diet quality systematic review",
    "diet quality meta-analysis",
    "dietary fiber systematic review",
    "dietary fibre systematic review",
    "whole grain systematic review",
    "carbohydrate quality systematic review",
    "low glycemic index systematic review",
    "low glycaemic index systematic review",
    "DASH eating plan guideline",
    "DASH dietary pattern guideline",
    "Mediterranean eating pattern guideline",
    "Mediterranean diet guideline",
    "MIND diet systematic review",
    "portfolio diet systematic review",
    "plant protein systematic review",
    "plant-based protein systematic review",
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


def apply_diet_quality_extensions() -> None:
    for block_name in (
        "lifestyle_nutrition_patterns",
        "cardiometabolic_precision",
        "adherence_persistence",
    ):
        _extend_semantic_block(
            block_name,
            terms=CARDIOMETABOLIC_DIET_QUALITY_TERMS,
            document_terms=CARDIOMETABOLIC_DIET_QUALITY_DOCUMENT_TERMS,
        )
