from __future__ import annotations

from nutev.querypacks import semantic_blocks

DIABETES_REMISSION_NUTRITION_TERMS = [
    "diet-induced diabetes remission",
    "diet induced diabetes remission",
    "lifestyle-induced diabetes remission",
    "lifestyle induced diabetes remission",
    "nutrition-induced diabetes remission",
    "nutrition induced diabetes remission",
    "dietary intervention diabetes remission",
    "nutrition therapy diabetes remission",
    "medical nutrition therapy diabetes remission",
    "meal replacement diabetes remission",
    "total diet replacement diabetes remission",
    "low energy diet diabetes remission",
    "low calorie diet diabetes remission",
    "very low energy diet diabetes remission",
    "very low calorie diet diabetes remission",
    "formula diet diabetes remission",
]

DIABETES_REMISSION_NUTRITION_DOCUMENT_TERMS = [
    "diabetes remission nutrition intervention",
    "type 2 diabetes remission nutrition intervention",
    "diabetes remission dietary intervention",
    "type 2 diabetes remission dietary intervention",
    "diabetes remission medical nutrition therapy",
    "diabetes remission meal replacement trial",
    "diabetes remission total diet replacement trial",
    "diabetes remission low energy diet trial",
    "diabetes remission low calorie diet trial",
    "diabetes remission program evaluation",
    "type 2 diabetes remission program evaluation",
]

WEIGHT_MAINTENANCE_NUTRITION_TERMS = [
    "weight maintenance nutrition intervention",
    "weight maintenance dietary intervention",
    "weight loss maintenance nutrition intervention",
    "weight loss maintenance dietary intervention",
    "post-weight loss nutrition intervention",
    "post weight loss nutrition intervention",
    "post-weight loss dietary intervention",
    "post weight loss dietary intervention",
    "weight regain prevention nutrition intervention",
    "weight regain prevention dietary intervention",
]

WEIGHT_MAINTENANCE_NUTRITION_DOCUMENT_TERMS = [
    "weight maintenance nutrition trial",
    "weight maintenance dietary trial",
    "weight loss maintenance nutrition trial",
    "weight loss maintenance dietary trial",
    "weight regain prevention nutrition trial",
    "weight regain prevention dietary trial",
    "weight maintenance nutrition systematic review",
    "weight loss maintenance dietary systematic review",
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


def apply_remission_nutrition_extensions() -> None:
    nutrition_anchored_terms = [
        *DIABETES_REMISSION_NUTRITION_TERMS,
        *WEIGHT_MAINTENANCE_NUTRITION_TERMS,
    ]
    nutrition_anchored_document_terms = [
        *DIABETES_REMISSION_NUTRITION_DOCUMENT_TERMS,
        *WEIGHT_MAINTENANCE_NUTRITION_DOCUMENT_TERMS,
    ]
    for block_name in (
        "adherence_persistence",
        "cardiometabolic_precision",
        "implementation_science",
        "lifestyle_nutrition_patterns",
        "nutrition_care_delivery",
    ):
        _extend_semantic_block(
            block_name,
            terms=nutrition_anchored_terms,
            document_terms=nutrition_anchored_document_terms,
        )
