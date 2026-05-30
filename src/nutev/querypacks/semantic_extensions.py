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

NUTRITION_IMPLEMENTATION_TERMS = [
    "nutrition implementation",
    "diet implementation",
    "dietary implementation",
    "nutrition intervention implementation",
    "dietary intervention implementation",
    "implementation of nutrition interventions",
    "implementation of dietary interventions",
    "nutrition behavior change intervention",
    "nutrition behaviour change intervention",
    "dietary behavior change intervention",
    "dietary behaviour change intervention",
    "dietary self-management support",
    "nutrition self-management support",
]

NUTRITION_IMPLEMENTATION_DOCUMENT_TERMS = [
    "nutrition implementation study",
    "dietary implementation study",
    "nutrition implementation trial",
    "dietary implementation trial",
    "nutrition intervention implementation study",
    "dietary intervention implementation study",
    "nutrition behavior change trial",
    "nutrition behaviour change trial",
]

CULINARY_FOOD_SKILLS_IMPLEMENTATION_TERMS = [
    "culinary medicine intervention",
    "culinary medicine program",
    "culinary medicine programme",
    "teaching kitchen intervention",
    "teaching kitchen program",
    "teaching kitchen programme",
    "cooking skills intervention",
    "home cooking intervention",
    "food literacy intervention",
    "nutrition literacy intervention",
    "food skills intervention",
    "meal planning intervention",
    "healthy grocery shopping intervention",
]

CULINARY_FOOD_SKILLS_DOCUMENT_TERMS = [
    "culinary medicine intervention",
    "teaching kitchen intervention",
    "teaching kitchen curriculum",
    "cooking skills intervention",
    "food literacy intervention",
    "nutrition literacy intervention",
    "meal planning intervention",
    "food skills intervention",
]

DIET_ADHERENCE_PRECISION_TERMS = [
    "diet adherence",
    "dietary adherence intervention",
    "adherence to dietary intervention",
    "adherence to nutrition intervention",
    "diet quality maintenance",
    "dietary maintenance intervention",
    "dietary self-efficacy",
    "nutrition self-efficacy",
]

DIET_ADHERENCE_PRECISION_DOCUMENT_TERMS = [
    "dietary adherence intervention",
    "dietary maintenance trial",
    "diet quality maintenance trial",
    "adherence to dietary intervention",
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
        "implementation_science",
        terms=NUTRITION_IMPLEMENTATION_TERMS,
        document_terms=NUTRITION_IMPLEMENTATION_DOCUMENT_TERMS,
    )
    _extend_semantic_block(
        "adherence_persistence",
        terms=DIET_ADHERENCE_PRECISION_TERMS,
        document_terms=DIET_ADHERENCE_PRECISION_DOCUMENT_TERMS,
    )
    _extend_semantic_block(
        "food_literacy_agency",
        terms=CULINARY_FOOD_SKILLS_IMPLEMENTATION_TERMS,
        document_terms=CULINARY_FOOD_SKILLS_DOCUMENT_TERMS,
    )


apply_semantic_extensions()
