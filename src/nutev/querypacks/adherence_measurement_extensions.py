from __future__ import annotations

from nutev.querypacks import semantic_blocks

DIETARY_ADHERENCE_MEASUREMENT_TERMS = [
    "dietary adherence assessment",
    "dietary adherence measure",
    "dietary adherence measures",
    "dietary adherence measurement",
    "dietary adherence questionnaire",
    "dietary adherence scale",
    "dietary adherence score",
    "diet adherence score",
    "dietary adherence index",
    "diet adherence index",
    "diet quality adherence",
    "dietary pattern adherence",
    "meal plan adherence",
    "meal-plan adherence",
    "adherence to dietary advice",
    "adherence to dietary recommendations",
    "nutrition adherence counseling",
    "nutrition adherence counselling",
    "mediterranean diet adherence",
    "dash diet adherence",
    "plant-based diet adherence",
    "plant based diet adherence",
    "low-carbohydrate diet adherence",
    "low carbohydrate diet adherence",
]

DIETARY_ADHERENCE_MEASUREMENT_DOCUMENT_TERMS = [
    "dietary adherence assessment",
    "dietary adherence questionnaire",
    "dietary adherence scale",
    "dietary adherence score validation",
    "dietary adherence index validation",
    "dietary pattern adherence score",
    "meal plan adherence intervention",
    "adherence to dietary advice intervention",
    "mediterranean diet adherence score",
    "dash diet adherence score",
    "plant-based diet adherence score",
    "plant based diet adherence score",
    "low-carbohydrate diet adherence trial",
    "low carbohydrate diet adherence trial",
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


def _extend_block(
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


def apply_adherence_measurement_extensions() -> None:
    for block_name in ("adherence_persistence", "lifestyle_nutrition_patterns"):
        _extend_block(
            block_name,
            terms=DIETARY_ADHERENCE_MEASUREMENT_TERMS,
            document_terms=DIETARY_ADHERENCE_MEASUREMENT_DOCUMENT_TERMS,
        )


apply_adherence_measurement_extensions()
