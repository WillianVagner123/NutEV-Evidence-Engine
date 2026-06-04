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
    "cardiorenal metabolic syndrome",
    "cardiorenal-metabolic syndrome",
    "cardiorenal metabolic health",
    "cardiorenal-metabolic health",
    "cardiorenal metabolic risk",
    "cardiorenal-metabolic risk",
    "kidney cardiometabolic health",
    "kidney cardiometabolic risk",
]

CARDIOVASCULAR_KIDNEY_METABOLIC_DOCUMENT_TERMS = [
    "scientific statement",
    "presidential advisory",
    "advisory statement",
    "clinical practice guideline",
    "consensus statement",
    "consensus report",
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

DIET_QUALITY_INDEX_TERMS = [
    "diet quality index",
    "diet quality indices",
    "diet quality score",
    "diet quality scores",
    "healthy eating index",
    "alternate healthy eating index",
    "ahei",
    "dietary quality score",
    "dietary quality scores",
    "dietary pattern score",
    "dietary pattern scores",
    "mediterranean diet score",
    "mediterranean dietary score",
    "dash score",
    "dash diet score",
    "plant-based diet index",
    "plant based diet index",
    "healthy plant-based diet index",
    "healthy plant based diet index",
    "provegetarian food pattern",
    "pro-vegetarian food pattern",
    "dietary inflammatory index",
    "nova score",
    "ultra-processed food score",
]

DIET_QUALITY_INDEX_DOCUMENT_TERMS = [
    "diet quality index validation",
    "diet quality score validation",
    "healthy eating index validation",
    "dietary pattern score validation",
    "dietary adherence score",
    "dietary adherence scores",
    "mediterranean diet adherence score",
    "dash adherence score",
    "plant-based diet index validation",
    "plant based diet index validation",
]

OFFICIAL_GUIDANCE_TERMS = [
    "evidence-based guideline",
    "evidence based guideline",
    "evidence-based guidance",
    "evidence based guidance",
    "recommendation statement",
    "clinical recommendation statement",
    "official recommendation",
    "official recommendations",
    "position statement",
    "position paper",
    "expert consensus",
    "expert consensus statement",
    "clinical consensus statement",
    "society guideline",
    "society guidelines",
    "professional society statement",
]

OFFICIAL_GUIDANCE_DOCUMENT_TERMS = [
    "evidence-based guideline",
    "evidence based guideline",
    "evidence-based guidance",
    "evidence based guidance",
    "recommendation statement",
    "clinical recommendation statement",
    "position statement",
    "position paper",
    "expert consensus",
    "expert consensus statement",
    "clinical consensus statement",
    "society guideline",
    "society guidelines",
    "professional society statement",
]

SOCIAL_NEEDS_FOOD_ACCESS_TERMS = [
    "food insecurity intervention",
    "food insecurity screening",
    "screening for food insecurity",
    "hunger vital sign",
    "nutrition security screening",
    "social needs screening",
    "social needs intervention",
    "social determinants of health",
    "community-based nutrition intervention",
    "community based nutrition intervention",
    "community health worker nutrition",
    "community health worker lifestyle",
    "healthy food access",
    "access to healthy food",
    "healthy food retail",
    "food pantry intervention",
    "food pantry referral",
    "food pharmacy",
    "food pharmacy program",
    "social prescribing nutrition",
    "social prescribing for food insecurity",
]

SOCIAL_NEEDS_FOOD_ACCESS_DOCUMENT_TERMS = [
    "food insecurity screening program",
    "social needs screening program",
    "community-based intervention",
    "community based intervention",
    "community health worker intervention",
    "food pantry intervention",
    "food pharmacy program",
    "social prescribing program",
    "policy evaluation",
    "implementation study",
    "quality improvement study",
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
        "evidence_synthesis",
        terms=OFFICIAL_GUIDANCE_TERMS,
        document_terms=OFFICIAL_GUIDANCE_DOCUMENT_TERMS,
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
    for block_name in ("adherence_persistence", "lifestyle_nutrition_patterns"):
        _extend_semantic_block(
            block_name,
            terms=DIET_QUALITY_INDEX_TERMS,
            document_terms=DIET_QUALITY_INDEX_DOCUMENT_TERMS,
        )
    _extend_semantic_block(
        "food_literacy_agency",
        terms=FOOD_SKILLS_SELF_EFFICACY_TERMS,
        document_terms=FOOD_SKILLS_SELF_EFFICACY_DOCUMENT_TERMS,
    )
    for block_name in ("equity_access", "food_prescription_programs"):
        _extend_semantic_block(
            block_name,
            terms=SOCIAL_NEEDS_FOOD_ACCESS_TERMS,
            document_terms=SOCIAL_NEEDS_FOOD_ACCESS_DOCUMENT_TERMS,
        )


apply_semantic_extensions()
