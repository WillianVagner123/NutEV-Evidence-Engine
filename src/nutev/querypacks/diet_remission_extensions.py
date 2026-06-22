from __future__ import annotations

from nutev.querypacks import semantic_blocks

DIET_REMISSION_REPLACEMENT_TERMS = [
    "total diet replacement",
    "total diet replacements",
    "total diet replacement program",
    "total diet replacement programme",
    "low energy total diet replacement",
    "low-energy total diet replacement",
    "very low energy diet",
    "very-low-energy diet",
    "very low energy diet program",
    "very low energy diet programme",
    "very low calorie diet",
    "very-low-calorie diet",
    "very low calorie diet program",
    "very low calorie diet programme",
    "formula diet",
    "formula diets",
    "formula diet program",
    "formula diet programme",
    "diabetes remission program",
    "diabetes remission programme",
    "type 2 diabetes remission program",
    "type 2 diabetes remission programme",
    "DiRECT trial",
    "Counterweight Plus",
]

DIET_REMISSION_REPLACEMENT_DOCUMENT_TERMS = [
    "total diet replacement trial",
    "total diet replacement systematic review",
    "total diet replacement intervention",
    "low energy total diet replacement trial",
    "low-energy total diet replacement trial",
    "very low energy diet trial",
    "very low calorie diet trial",
    "formula diet trial",
    "diabetes remission program evaluation",
    "diabetes remission programme evaluation",
    "type 2 diabetes remission program evaluation",
    "type 2 diabetes remission programme evaluation",
    "DiRECT trial",
    "Counterweight Plus intervention",
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


def apply_diet_remission_replacement_extensions() -> None:
    for block_name in (
        "adherence_persistence",
        "cardiometabolic_precision",
        "lifestyle_nutrition_patterns",
    ):
        _extend_semantic_block(
            block_name,
            terms=DIET_REMISSION_REPLACEMENT_TERMS,
            document_terms=DIET_REMISSION_REPLACEMENT_DOCUMENT_TERMS,
        )
