from __future__ import annotations

from nutev.querypacks import semantic_blocks

THERAPEUTIC_WEIGHT_LOSS_DIET_TERMS = [
    "meal replacement",
    "meal replacements",
    "partial meal replacement",
    "partial meal replacements",
    "total diet replacement",
    "total diet replacements",
    "total diet replacement program",
    "total diet replacement programme",
    "formula diet",
    "formula diets",
    "formula low-energy diet",
    "formula low energy diet",
    "low-calorie diet",
    "low calorie diet",
    "low-energy diet",
    "low energy diet",
    "very-low-calorie diet",
    "very low calorie diet",
    "very-low-energy diet",
    "very low energy diet",
    "dietary energy restriction",
    "energy-restricted diet",
    "energy restricted diet",
    "calorie restriction diet",
    "calorie-restricted diet",
    "structured meal plan",
    "structured meal plans",
]

THERAPEUTIC_WEIGHT_LOSS_DIET_DOCUMENT_TERMS = [
    "meal replacement trial",
    "meal replacement systematic review",
    "partial meal replacement trial",
    "total diet replacement trial",
    "total diet replacement systematic review",
    "total diet replacement program evaluation",
    "total diet replacement programme evaluation",
    "formula diet trial",
    "low-calorie diet trial",
    "low calorie diet trial",
    "low-energy diet trial",
    "low energy diet trial",
    "very-low-calorie diet trial",
    "very low calorie diet trial",
    "very-low-energy diet trial",
    "very low energy diet trial",
    "energy-restricted diet trial",
    "energy restricted diet trial",
    "diabetes remission diet trial",
    "type 2 diabetes remission diet trial",
    "weight loss maintenance diet trial",
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


def apply_therapeutic_diet_extensions() -> None:
    for block_name in (
        "lifestyle_nutrition_patterns",
        "adherence_persistence",
        "cardiometabolic_precision",
        "nutrition_care_delivery",
    ):
        _extend_semantic_block(
            block_name,
            terms=THERAPEUTIC_WEIGHT_LOSS_DIET_TERMS,
            document_terms=THERAPEUTIC_WEIGHT_LOSS_DIET_DOCUMENT_TERMS,
        )
