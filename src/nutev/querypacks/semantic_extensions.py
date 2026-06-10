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

METABOLIC_REMISSION_MAINTENANCE_TERMS = [
    "type 2 diabetes remission",
    "diabetes remission",
    "remission of type 2 diabetes",
    "glycemic remission",
    "glycaemic remission",
    "diabetes reversal",
    "type 2 diabetes reversal",
    "metabolic remission",
    "weight loss maintenance",
    "long-term weight loss maintenance",
    "long term weight loss maintenance",
    "weight regain prevention",
    "weight regain management",
]

METABOLIC_REMISSION_MAINTENANCE_DOCUMENT_TERMS = [
    "diabetes remission consensus",
    "diabetes remission consensus report",
    "type 2 diabetes remission guideline",
    "type 2 diabetes remission consensus",
    "remission consensus",
    "remission guideline",
    "weight loss maintenance trial",
    "weight loss maintenance systematic review",
    "weight regain prevention trial",
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

SUSTAINABLE_DIETARY_GUIDANCE_TERMS = [
    "sustainable healthy diet",
    "sustainable healthy diets",
    "healthy sustainable diet",
    "healthy sustainable diets",
    "healthy and sustainable diet",
    "healthy and sustainable diets",
    "sustainable dietary pattern",
    "sustainable dietary patterns",
    "planetary diet",
    "planetary health diet",
    "eat-lancet diet",
    "eat-lancet planetary health diet",
    "sustainable food-based dietary guideline",
    "sustainable food-based dietary guidelines",
    "sustainable food based dietary guideline",
    "sustainable food based dietary guidelines",
    "sustainable dietary guideline",
    "sustainable dietary guidelines",
    "food-based dietary guideline sustainability",
    "food based dietary guideline sustainability",
    "dietary guidelines sustainability",
    "climate-friendly diet",
    "climate friendly diet",
]

SUSTAINABLE_DIETARY_GUIDANCE_DOCUMENT_TERMS = [
    "sustainable healthy diet guideline",
    "sustainable healthy diets guideline",
    "sustainable food-based dietary guideline",
    "sustainable food-based dietary guidelines",
    "sustainable food based dietary guideline",
    "sustainable food based dietary guidelines",
    "sustainable dietary guideline",
    "sustainable dietary guidelines",
    "planetary health diet guideline",
    "eat-lancet guideline",
    "food-based dietary guideline sustainability",
    "food based dietary guideline sustainability",
    "healthy sustainable diets policy brief",
    "sustainable diets policy brief",
    "sustainable diets position statement",
    "sustainable diets systematic review",
]

PRECISION_PERSONALIZED_NUTRITION_TERMS = [
    "personalized nutrition for cardiometabolic risk",
    "personalised nutrition for cardiometabolic risk",
    "personalized nutrition for obesity",
    "personalised nutrition for obesity",
    "personalized nutrition for type 2 diabetes",
    "personalised nutrition for type 2 diabetes",
    "precision nutrition for cardiometabolic risk",
    "precision nutrition for obesity",
    "precision nutrition for type 2 diabetes",
    "tailored dietary advice for cardiometabolic risk",
    "tailored dietary advice for obesity",
    "tailored dietary advice for type 2 diabetes",
    "tailored dietary intervention for cardiometabolic risk",
    "tailored dietary intervention for obesity",
    "tailored dietary intervention for type 2 diabetes",
    "personalized dietary intervention for cardiometabolic risk",
    "personalised dietary intervention for cardiometabolic risk",
    "individualized dietary intervention for obesity",
    "individualised dietary intervention for obesity",
    "individualized dietary intervention for type 2 diabetes",
    "individualised dietary intervention for type 2 diabetes",
]

PRECISION_PERSONALIZED_NUTRITION_DOCUMENT_TERMS = [
    "personalized nutrition intervention",
    "personalised nutrition intervention",
    "precision nutrition intervention",
    "tailored dietary advice intervention",
    "tailored dietary intervention",
    "personalized dietary intervention",
    "personalised dietary intervention",
    "individualized dietary intervention",
    "individualised dietary intervention",
    "personalized nutrition framework",
    "personalised nutrition framework",
    "precision nutrition framework",
    "tailored nutrition framework",
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
    "nutrition assistance program",
    "nutrition assistance intervention",
    "healthy food assistance",
    "healthy food benefit",
    "healthy food benefits",
    "food benefit program",
    "food resource referral",
    "food resource navigation",
    "produce prescription referral",
    "food as medicine referral",
    "food is medicine referral",
    "medically tailored meal referral",
    "medically tailored grocery referral",
    "fresh food pharmacy",
    "fruit and vegetable incentive",
    "fruit and vegetable incentives",
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
    "nutrition assistance program",
    "nutrition assistance intervention",
    "healthy food benefit program",
    "food resource referral program",
    "produce prescription referral program",
    "food as medicine referral program",
    "food is medicine referral program",
    "medically tailored meal referral program",
    "fresh food pharmacy program",
    "fruit and vegetable incentive program",
]

FOOD_AS_MEDICINE_REFERRAL_TERMS = [
    "food as medicine clinic",
    "food is medicine clinic",
    "food as medicine program",
    "food is medicine program",
    "food as medicine programme",
    "food is medicine programme",
    "food pharmacy referral",
    "food pharmacy intervention",
    "food pharmacy implementation",
    "fresh food pharmacy intervention",
    "produce prescription implementation",
    "produce prescription evaluation",
    "produce prescription intervention",
    "produce prescription trial",
    "healthy food prescription intervention",
    "medically tailored groceries intervention",
    "medically tailored grocery intervention",
    "medically tailored meals intervention",
    "medically tailored meal intervention",
    "medically tailored food intervention",
    "nutrition security intervention",
    "nutrition security program",
    "nutrition security programme",
    "food resource navigation program",
    "food resource navigation intervention",
    "community food referral",
    "clinical-community food referral",
    "clinical community food referral",
]

FOOD_AS_MEDICINE_REFERRAL_DOCUMENT_TERMS = [
    "food as medicine implementation study",
    "food is medicine implementation study",
    "food as medicine program evaluation",
    "food is medicine program evaluation",
    "food pharmacy implementation study",
    "food pharmacy program evaluation",
    "produce prescription implementation study",
    "produce prescription program evaluation",
    "produce prescription intervention trial",
    "healthy food prescription intervention trial",
    "medically tailored meal intervention trial",
    "medically tailored meals program evaluation",
    "medically tailored grocery program evaluation",
    "nutrition security intervention trial",
    "nutrition security program evaluation",
    "food resource navigation program evaluation",
    "clinical-community food referral program",
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
        terms=OFFICIAL_GUIDANCE_TERMS + SUSTAINABLE_DIETARY_GUIDANCE_TERMS,
        document_terms=OFFICIAL_GUIDANCE_DOCUMENT_TERMS
        + SUSTAINABLE_DIETARY_GUIDANCE_DOCUMENT_TERMS,
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
    for block_name in (
        "adherence_persistence",
        "cardiometabolic_precision",
        "lifestyle_nutrition_patterns",
    ):
        _extend_semantic_block(
            block_name,
            terms=METABOLIC_REMISSION_MAINTENANCE_TERMS,
            document_terms=METABOLIC_REMISSION_MAINTENANCE_DOCUMENT_TERMS,
        )
        _extend_semantic_block(
            block_name,
            terms=PRECISION_PERSONALIZED_NUTRITION_TERMS,
            document_terms=PRECISION_PERSONALIZED_NUTRITION_DOCUMENT_TERMS,
        )
    for block_name in ("adherence_persistence", "lifestyle_nutrition_patterns"):
        _extend_semantic_block(
            block_name,
            terms=DIET_QUALITY_INDEX_TERMS,
            document_terms=DIET_QUALITY_INDEX_DOCUMENT_TERMS,
        )
    _extend_semantic_block(
        "lifestyle_nutrition_patterns",
        terms=SUSTAINABLE_DIETARY_GUIDANCE_TERMS,
        document_terms=SUSTAINABLE_DIETARY_GUIDANCE_DOCUMENT_TERMS,
    )
    _extend_semantic_block(
        "food_literacy_agency",
        terms=FOOD_SKILLS_SELF_EFFICACY_TERMS,
        document_terms=FOOD_SKILLS_SELF_EFFICACY_DOCUMENT_TERMS,
    )
    for block_name in ("equity_access", "food_prescription_programs"):
        _extend_semantic_block(
            block_name,
            terms=SOCIAL_NEEDS_FOOD_ACCESS_TERMS + FOOD_AS_MEDICINE_REFERRAL_TERMS,
            document_terms=SOCIAL_NEEDS_FOOD_ACCESS_DOCUMENT_TERMS
            + FOOD_AS_MEDICINE_REFERRAL_DOCUMENT_TERMS,
        )
    _extend_semantic_block(
        "implementation_science",
        terms=FOOD_AS_MEDICINE_REFERRAL_TERMS,
        document_terms=FOOD_AS_MEDICINE_REFERRAL_DOCUMENT_TERMS,
    )


apply_semantic_extensions()
