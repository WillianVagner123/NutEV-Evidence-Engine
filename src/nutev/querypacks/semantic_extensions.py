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

METABOLIC_LIVER_STEATOSIS_TERMS = [
    "hepatic steatosis",
    "liver steatosis",
    "hepatic fat",
    "liver fat",
    "intrahepatic fat",
    "intra-hepatic fat",
    "intrahepatic triglyceride",
    "intrahepatic triglycerides",
    "liver fat content",
    "hepatic fat content",
]

METABOLIC_LIVER_STEATOSIS_DOCUMENT_TERMS = [
    "hepatic steatosis guideline",
    "steatotic liver disease guideline",
    "masld practice guidance",
    "nafld practice guidance",
    "mash clinical practice guideline",
    "liver fat systematic review",
    "hepatic steatosis systematic review",
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
    "culinary medicine program",
    "culinary medicine programme",
    "culinary medicine intervention",
    "culinary nutrition program",
    "culinary nutrition programme",
    "culinary nutrition intervention",
    "teaching kitchen program",
    "teaching kitchen programme",
    "teaching kitchen intervention",
    "food skills intervention",
    "cooking skills intervention",
    "meal planning intervention",
    "meal preparation intervention",
    "hands-on cooking",
    "hands on cooking",
    "cooking education",
    "culinary education",
    "nutrition education intervention",
    "culinary medicine referral",
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
    "culinary medicine program",
    "culinary medicine programme",
    "culinary medicine intervention",
    "culinary nutrition program",
    "culinary nutrition programme",
    "culinary nutrition intervention",
    "teaching kitchen program",
    "teaching kitchen programme",
    "teaching kitchen intervention",
    "food skills intervention",
    "cooking skills intervention",
    "meal planning intervention",
    "meal preparation intervention",
    "nutrition education intervention",
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
    _extend_semantic_block(
        "cardiometabolic_liver",
        terms=METABOLIC_LIVER_STEATOSIS_TERMS,
        document_terms=METABOLIC_LIVER_STEATOSIS_DOCUMENT_TERMS,
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


apply_semantic_extensions()
