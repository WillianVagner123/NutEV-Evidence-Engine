from __future__ import annotations

from nutev.querypacks import semantic_blocks

SUSTAINABLE_DIET_TERMS = [
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
    "sustainable food-based dietary guideline",
    "sustainable food based dietary guideline",
    "plant-forward diet",
    "plant forward diet",
    "planetary health dietary pattern",
]

SUSTAINABLE_DIET_DOCUMENT_TERMS = [
    "sustainable healthy diets guideline",
    "sustainable healthy diet guideline",
    "healthy and sustainable diets guideline",
    "healthy sustainable diets guideline",
    "sustainable dietary patterns guideline",
    "sustainable food-based dietary guideline",
    "sustainable food based dietary guideline",
    "sustainable diet consensus",
    "sustainable diets consensus",
    "sustainable diet systematic review",
    "sustainable diets systematic review",
    "sustainable dietary patterns systematic review",
    "sustainable diet umbrella review",
    "sustainable diets umbrella review",
    "planetary health diet systematic review",
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
    for block_name in ("lifestyle_nutrition_patterns", "evidence_synthesis"):
        _extend_semantic_block(
            block_name,
            terms=SUSTAINABLE_DIET_TERMS,
            document_terms=SUSTAINABLE_DIET_DOCUMENT_TERMS,
        )
