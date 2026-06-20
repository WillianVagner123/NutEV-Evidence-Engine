from __future__ import annotations

from nutev.querypacks import semantic_blocks

SUSTAINABLE_DIET_PATTERN_TERMS = [
    "sustainable healthy diet",
    "sustainable healthy diets",
    "healthy sustainable diet",
    "healthy sustainable diets",
    "healthy and sustainable diet",
    "healthy and sustainable diets",
    "sustainable dietary pattern",
    "sustainable dietary patterns",
    "sustainable diet",
    "sustainable diets",
    "planetary diet",
    "planetary diets",
    "planetary health diet",
    "planetary health diets",
    "eat-lancet diet",
    "eat-lancet diets",
    "eat-lancet reference diet",
    "eat lancet diet",
    "eat lancet diets",
    "eat lancet reference diet",
]

SUSTAINABLE_DIET_PATTERN_DOCUMENT_TERMS = [
    "sustainable healthy diet guideline",
    "sustainable healthy diets guideline",
    "healthy and sustainable diet guideline",
    "healthy and sustainable diets guideline",
    "sustainable dietary guideline",
    "sustainable dietary guidelines",
    "sustainable dietary pattern systematic review",
    "sustainable dietary patterns systematic review",
    "sustainable diet systematic review",
    "sustainable diets systematic review",
    "planetary health diet systematic review",
    "planetary health diets systematic review",
    "eat-lancet diet systematic review",
    "eat-lancet reference diet systematic review",
    "eat lancet diet systematic review",
    "eat lancet reference diet systematic review",
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


def apply_sustainable_diet_extensions() -> None:
    _extend_semantic_block(
        "lifestyle_nutrition_patterns",
        terms=SUSTAINABLE_DIET_PATTERN_TERMS,
        document_terms=SUSTAINABLE_DIET_PATTERN_DOCUMENT_TERMS,
    )
    _extend_semantic_block(
        "evidence_synthesis",
        terms=SUSTAINABLE_DIET_PATTERN_TERMS,
        document_terms=SUSTAINABLE_DIET_PATTERN_DOCUMENT_TERMS,
    )


apply_sustainable_diet_extensions()
