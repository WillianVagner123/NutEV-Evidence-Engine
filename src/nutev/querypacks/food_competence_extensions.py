from __future__ import annotations

from nutev.querypacks import semantic_blocks

FOOD_COMPETENCE_BEHAVIOR_TERMS = [
    "food competence",
    "food competence intervention",
    "food competence framework",
    "food competence model",
    "food competence program",
    "food competence programme",
    "eating competence",
    "eating competence intervention",
    "eating competence framework",
    "eating competence model",
    "eating competence approach",
    "Satter eating competence",
    "ecSatter",
    "food skills confidence",
    "food skills self-efficacy",
    "food skills self efficacy",
    "food preparation confidence",
    "food preparation self-efficacy",
    "food preparation self efficacy",
    "meal preparation confidence",
    "meal preparation self-efficacy",
    "meal preparation self efficacy",
    "meal planning self-efficacy",
    "meal planning self efficacy",
    "cooking self-efficacy",
    "cooking self efficacy",
    "culinary self-efficacy",
    "culinary self efficacy",
    "kitchen confidence",
    "healthy cooking confidence",
    "healthy cooking self-efficacy",
    "healthy cooking self efficacy",
    "healthy grocery shopping skills",
    "healthy shopping skills",
]

FOOD_COMPETENCE_INSTRUMENT_TERMS = [
    "food competence scale",
    "food competence questionnaire",
    "food competence instrument",
    "food competence inventory",
    "food skills scale",
    "food skills questionnaire",
    "food skills instrument",
    "food skills assessment",
    "food preparation skills scale",
    "food preparation skills questionnaire",
    "meal preparation skills scale",
    "meal preparation skills questionnaire",
    "meal planning questionnaire",
    "meal planning scale",
    "cooking self-efficacy scale",
    "cooking self efficacy scale",
    "cooking self-efficacy questionnaire",
    "cooking self efficacy questionnaire",
    "culinary self-efficacy scale",
    "culinary self efficacy scale",
    "cooking confidence scale",
    "kitchen confidence scale",
    "eating competence scale",
    "eating competence questionnaire",
    "eating competence instrument",
    "eating competence inventory",
    "Satter eating competence inventory",
    "ecSatter inventory",
    "eating competence validation",
    "food competence validation",
    "food skills validation",
    "culinary skills validation",
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


def apply_food_competence_extensions() -> None:
    _extend_semantic_block(
        "food_literacy_agency",
        terms=FOOD_COMPETENCE_BEHAVIOR_TERMS,
        document_terms=FOOD_COMPETENCE_INSTRUMENT_TERMS,
    )
    _extend_semantic_block(
        "adherence_persistence",
        terms=FOOD_COMPETENCE_BEHAVIOR_TERMS,
        document_terms=FOOD_COMPETENCE_INSTRUMENT_TERMS,
    )
