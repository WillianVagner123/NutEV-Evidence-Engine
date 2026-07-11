from __future__ import annotations

from nutev.querypacks import semantic_blocks

FOOD_LITERACY_MEASUREMENT_TERMS = [
    "food literacy assessment",
    "food literacy measurement",
    "food literacy measure",
    "food literacy measures",
    "food literacy scale",
    "food literacy questionnaire",
    "food literacy survey",
    "food literacy instrument",
    "food literacy framework",
    "functional food literacy",
    "interactive food literacy",
    "critical food literacy",
    "food and nutrition literacy",
    "food and nutrition literacy questionnaire",
    "food and nutrition literacy scale",
    "food and nutrition literacy instrument",
    "nutrition literacy assessment",
    "nutrition literacy measurement",
    "nutrition literacy measure",
    "nutrition literacy scale",
    "nutrition literacy questionnaire",
    "nutrition literacy instrument",
    "nutrition literacy survey",
    "dietary literacy",
    "dietary literacy scale",
    "dietary literacy questionnaire",
    "food skills assessment",
    "food skills measurement",
    "food skills measure",
    "food skills questionnaire",
    "food skills scale",
    "food skills survey",
    "food agency scale",
    "food agency questionnaire",
    "cooking skills scale",
    "cooking skills questionnaire",
    "cooking skills assessment",
    "meal planning questionnaire",
    "meal planning scale",
    "healthy eating self-efficacy",
    "healthy eating self efficacy",
    "dietary self-efficacy",
    "dietary self efficacy",
]

FOOD_LITERACY_MEASUREMENT_DOCUMENT_TERMS = [
    "food literacy questionnaire",
    "food literacy scale",
    "food literacy instrument",
    "food literacy validation",
    "food literacy assessment tool",
    "food literacy measure validation",
    "food literacy questionnaire validation",
    "food and nutrition literacy questionnaire",
    "food and nutrition literacy scale",
    "food and nutrition literacy instrument",
    "nutrition literacy questionnaire",
    "nutrition literacy scale",
    "nutrition literacy instrument",
    "nutrition literacy validation",
    "nutrition literacy assessment tool",
    "dietary literacy questionnaire",
    "dietary literacy scale",
    "food skills questionnaire",
    "food skills scale",
    "food skills validation",
    "food agency questionnaire",
    "food agency scale",
    "cooking skills questionnaire",
    "cooking skills scale",
    "cooking skills validation",
    "meal planning questionnaire",
    "meal planning scale",
    "healthy eating self-efficacy scale",
    "healthy eating self efficacy scale",
    "dietary self-efficacy scale",
    "dietary self efficacy scale",
    "psychometric validation",
    "scale development",
    "questionnaire validation",
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


def apply_food_literacy_measurement_extensions() -> None:
    block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS.setdefault(
        "food_literacy_agency",
        {"terms": [], "document_terms": []},
    )
    block["terms"] = _extend_unique(
        block.setdefault("terms", []),
        FOOD_LITERACY_MEASUREMENT_TERMS,
    )
    block["document_terms"] = _extend_unique(
        block.setdefault("document_terms", []),
        FOOD_LITERACY_MEASUREMENT_DOCUMENT_TERMS,
    )


apply_food_literacy_measurement_extensions()
