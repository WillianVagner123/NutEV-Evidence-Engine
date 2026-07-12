from __future__ import annotations

from nutev.querypacks import semantic_blocks

MEAL_STRUCTURE_ROUTINE_TERMS = [
    "structured meal plan",
    "structured meal plans",
    "structured meal planning",
    "meal structure",
    "meal structure intervention",
    "meal routine",
    "meal routines",
    "eating routine",
    "eating routines",
    "dietary routine",
    "dietary routines",
    "regular meal pattern",
    "regular meal patterns",
    "planned meals",
    "planned eating",
    "meal planning adherence",
    "meal preparation routine",
    "home meal preparation",
    "weekly meal planning",
    "family meal planning",
]

MEAL_STRUCTURE_ROUTINE_DOCUMENT_TERMS = [
    "meal planning intervention",
    "meal planning program",
    "meal planning programme",
    "structured meal plan intervention",
    "structured meal planning intervention",
    "meal routine intervention",
    "eating routine intervention",
    "dietary routine intervention",
    "meal preparation intervention",
    "home meal preparation intervention",
    "behavioral nutrition intervention",
    "behavioural nutrition intervention",
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


def apply_meal_structure_extensions() -> None:
    for block_name in (
        "adherence_persistence",
        "food_literacy_agency",
        "implementation_science",
        "lifestyle_nutrition_patterns",
        "commensality_context",
    ):
        _extend_semantic_block(
            block_name,
            terms=MEAL_STRUCTURE_ROUTINE_TERMS,
            document_terms=MEAL_STRUCTURE_ROUTINE_DOCUMENT_TERMS,
        )


apply_meal_structure_extensions()
