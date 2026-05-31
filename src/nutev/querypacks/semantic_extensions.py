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

INTENSIVE_LIFESTYLE_PROGRAM_TERMS = [
    "intensive lifestyle intervention",
    "intensive lifestyle interventions",
    "behavioral lifestyle intervention",
    "behavioural lifestyle intervention",
    "behavioral weight loss",
    "behavioural weight loss",
    "lifestyle weight management",
    "weight management program",
    "weight management programme",
    "diabetes prevention program",
    "diabetes prevention programme",
    "diabetes prevention programs",
    "diabetes prevention programmes",
    "weight loss maintenance",
]

INTENSIVE_LIFESTYLE_PROGRAM_DOCUMENT_TERMS = [
    "lifestyle intervention trial",
    "intensive lifestyle intervention trial",
    "behavioral weight loss trial",
    "behavioural weight loss trial",
    "weight loss maintenance trial",
    "diabetes prevention program",
    "diabetes prevention programme",
]

FOOD_SKILLS_SELF_EFFICACY_TERMS = [
    "cooking self-efficacy",
    "cooking self efficacy",
    "culinary self-efficacy",
    "culinary self efficacy",
    "food skills confidence",
    "food skills self-efficacy",
    "food skills self efficacy",
    "meal planning skills",
    "meal preparation skills",
    "healthy cooking skills",
    "healthy shopping skills",
    "nutrition label use",
    "food label use",
    "nutrition facts label",
    "front-of-package nutrition label",
    "front of package nutrition label",
]

FOOD_SKILLS_SELF_EFFICACY_DOCUMENT_TERMS = [
    "food skills questionnaire",
    "food skills assessment",
    "cooking self-efficacy scale",
    "cooking self efficacy scale",
    "culinary self-efficacy scale",
    "culinary self efficacy scale",
    "food literacy questionnaire",
    "nutrition literacy questionnaire",
    "nutrition label use questionnaire",
    "food label use questionnaire",
    "culinary medicine curriculum",
    "teaching kitchen curriculum",
]

FOOD_ENVIRONMENT_DIET_QUALITY_TERMS = [
    "food environment assessment",
    "food environment intervention",
    "food environment interventions",
    "healthy food retail",
    "healthy food retail intervention",
    "healthy food retail interventions",
    "grocery store intervention",
    "grocery store interventions",
    "supermarket intervention",
    "supermarket interventions",
    "food pantry intervention",
    "food pantry interventions",
    "food pantry nutrition",
    "healthy food pantry",
    "healthy food pantry intervention",
    "food desert",
    "food deserts",
    "food swamp",
    "food swamps",
    "diet quality index",
    "diet quality indices",
    "healthy eating index",
    "alternative healthy eating index",
    "mediterranean diet score",
]

FOOD_ENVIRONMENT_DIET_QUALITY_DOCUMENT_TERMS = [
    "food environment assessment",
    "food environment intervention",
    "healthy food retail intervention",
    "grocery store intervention",
    "supermarket intervention",
    "food pantry intervention",
    "diet quality index",
    "healthy eating index",
    "alternative healthy eating index",
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


def apply_semantic_extensions() -> None:
    _extend_semantic_block(
        "cardiometabolic_precision",
        terms=CARDIOVASCULAR_KIDNEY_METABOLIC_TERMS,
        document_terms=CARDIOVASCULAR_KIDNEY_METABOLIC_DOCUMENT_TERMS,
    )
    for block_name in (
        "implementation_science",
        "adherence_persistence",
        "lifestyle_nutrition_patterns",
    ):
        _extend_semantic_block(
            block_name,
            terms=INTENSIVE_LIFESTYLE_PROGRAM_TERMS,
            document_terms=INTENSIVE_LIFESTYLE_PROGRAM_DOCUMENT_TERMS,
        )
    _extend_semantic_block(
        "food_literacy_agency",
        terms=FOOD_SKILLS_SELF_EFFICACY_TERMS,
        document_terms=FOOD_SKILLS_SELF_EFFICACY_DOCUMENT_TERMS,
    )
    _extend_semantic_block(
        "food_literacy_agency",
        terms=FOOD_ENVIRONMENT_DIET_QUALITY_TERMS,
        document_terms=FOOD_ENVIRONMENT_DIET_QUALITY_DOCUMENT_TERMS,
    )
    _extend_semantic_block(
        "adherence_persistence",
        terms=FOOD_ENVIRONMENT_DIET_QUALITY_TERMS,
        document_terms=FOOD_ENVIRONMENT_DIET_QUALITY_DOCUMENT_TERMS,
    )


apply_semantic_extensions()
