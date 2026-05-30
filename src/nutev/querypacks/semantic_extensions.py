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

DIABETES_REMISSION_WEIGHT_MAINTENANCE_TERMS = [
    "diabetes remission",
    "type 2 diabetes remission",
    "diabetes reversal",
    "type 2 diabetes reversal",
    "glycemic remission",
    "glycaemic remission",
    "weight loss maintenance",
    "weight maintenance",
    "weight regain prevention",
    "prevention of weight regain",
    "long-term weight loss maintenance",
    "long term weight loss maintenance",
]

DIABETES_REMISSION_WEIGHT_MAINTENANCE_DOCUMENT_TERMS = [
    "clinical practice guideline",
    "consensus statement",
    "position statement",
    "scientific statement",
    "systematic review",
    "umbrella review",
    "randomized controlled trial",
    "pragmatic trial",
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
    precision_block["terms"] = _extend_unique(
        precision_block.setdefault("terms", []),
        DIABETES_REMISSION_WEIGHT_MAINTENANCE_TERMS,
    )
    precision_block["document_terms"] = _extend_unique(
        precision_block.setdefault("document_terms", []),
        CARDIOVASCULAR_KIDNEY_METABOLIC_DOCUMENT_TERMS,
    )
    precision_block["document_terms"] = _extend_unique(
        precision_block.setdefault("document_terms", []),
        DIABETES_REMISSION_WEIGHT_MAINTENANCE_DOCUMENT_TERMS,
    )


apply_semantic_extensions()
