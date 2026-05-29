from __future__ import annotations

from nutev.querypacks import semantic_blocks

CARDIOVASCULAR_KIDNEY_METABOLIC_TERMS = [
    "cardiovascular-kidney-metabolic syndrome",
    "cardiovascular kidney metabolic syndrome",
    "cardiovascular-kidney-metabolic health",
    "cardiovascular kidney metabolic health",
    "cardiovascular-kidney-metabolic risk",
    "cardiovascular kidney metabolic risk",
    "ckm syndrome",
    "ckm health",
    "ckm risk",
]

CARDIOVASCULAR_KIDNEY_METABOLIC_DOCUMENT_TERMS = [
    "scientific statement",
    "presidential advisory",
    "clinical practice guideline",
    "consensus statement",
    "clinical decision pathway",
    "practice guidance",
    "systematic review",
]

DIET_QUALITY_PATTERN_TERMS = [
    "healthy eating index",
    "alternate healthy eating index",
    "alternative healthy eating index",
    "diet quality index",
    "diet quality score",
    "dietary quality score",
    "dietary inflammatory index",
    "empirical dietary inflammatory pattern",
    "anti-inflammatory diet",
    "anti inflammatory diet",
    "prudent dietary pattern",
    "western dietary pattern",
]

DIET_QUALITY_PATTERN_DOCUMENT_TERMS = [
    "systematic review",
    "meta-analysis",
    "umbrella review",
    "scoping review",
    "dietary guideline",
    "food-based dietary guideline",
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


def apply_semantic_extensions() -> None:
    precision_block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS.setdefault(
        "cardiometabolic_precision",
        {"terms": [], "document_terms": []},
    )
    precision_block["terms"] = _extend_unique(
        precision_block.setdefault("terms", []),
        CARDIOVASCULAR_KIDNEY_METABOLIC_TERMS,
    )
    precision_block["document_terms"] = _extend_unique(
        precision_block.setdefault("document_terms", []),
        CARDIOVASCULAR_KIDNEY_METABOLIC_DOCUMENT_TERMS,
    )

    diet_pattern_block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS.setdefault(
        "lifestyle_nutrition_patterns",
        {"terms": [], "document_terms": []},
    )
    diet_pattern_block["terms"] = _extend_unique(
        diet_pattern_block.setdefault("terms", []),
        DIET_QUALITY_PATTERN_TERMS,
    )
    diet_pattern_block["document_terms"] = _extend_unique(
        diet_pattern_block.setdefault("document_terms", []),
        DIET_QUALITY_PATTERN_DOCUMENT_TERMS,
    )


apply_semantic_extensions()
