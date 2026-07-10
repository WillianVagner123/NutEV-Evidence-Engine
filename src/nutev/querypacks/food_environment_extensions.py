from __future__ import annotations

from nutev.querypacks import semantic_blocks

FOOD_ENVIRONMENT_CHOICE_TERMS = [
    "food choice architecture",
    "healthy choice architecture",
    "choice architecture intervention",
    "food environment nudge",
    "food environment nudging",
    "nutrition nudge",
    "nutrition nudging",
    "healthy food nudge",
    "healthy default",
    "healthy defaults",
    "default option",
    "healthy default option",
    "food placement",
    "healthy food placement",
    "product placement",
    "shelf placement",
    "healthy shelf placement",
    "point-of-purchase intervention",
    "point of purchase intervention",
    "point-of-choice intervention",
    "point of choice intervention",
    "cafeteria intervention",
    "cafeteria nudge",
    "worksite cafeteria intervention",
    "workplace cafeteria intervention",
    "supermarket intervention",
    "grocery store intervention",
    "healthy checkout",
    "healthy checkout intervention",
    "traffic light labeling",
    "traffic light labelling",
    "traffic light nutrition label",
    "menu calorie labeling",
    "menu calorie labelling",
]

FOOD_ENVIRONMENT_CHOICE_DOCUMENT_TERMS = [
    "choice architecture intervention",
    "food choice architecture intervention",
    "healthy choice architecture intervention",
    "food environment nudge intervention",
    "nutrition nudging intervention",
    "healthy default intervention",
    "food placement intervention",
    "point-of-purchase intervention",
    "point of purchase intervention",
    "point-of-choice intervention",
    "point of choice intervention",
    "cafeteria intervention trial",
    "supermarket intervention trial",
    "grocery store intervention trial",
    "healthy checkout intervention",
    "traffic light labeling intervention",
    "traffic light labelling intervention",
    "menu calorie labeling intervention",
    "menu calorie labelling intervention",
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


def apply_food_environment_choice_extensions() -> None:
    for block_name in (
        "food_literacy_agency",
        "implementation_science",
        "equity_access",
    ):
        _extend_semantic_block(
            block_name,
            terms=FOOD_ENVIRONMENT_CHOICE_TERMS,
            document_terms=FOOD_ENVIRONMENT_CHOICE_DOCUMENT_TERMS,
        )
