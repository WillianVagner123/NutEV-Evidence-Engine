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

FOOD_FARMACY_TERMS = [
    "food farmacy",
    "food farmacy program",
    "food farmacy intervention",
    "fresh food farmacy",
    "fresh food farmacy program",
    "fresh food farmacy intervention",
]

FOOD_FARMACY_DOCUMENT_TERMS = [
    "food farmacy program",
    "food farmacy intervention",
    "fresh food farmacy program",
    "fresh food farmacy intervention",
    "implementation study",
    "quality improvement study",
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
    "food pharmacy intervention",
    "food farmacy",
    "food farmacy program",
    "food farmacy intervention",
    "fresh food farmacy",
    "fresh food farmacy program",
    "fresh food farmacy intervention",
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
    "food pharmacy intervention",
    "food farmacy program",
    "food farmacy intervention",
    "fresh food farmacy program",
    "fresh food farmacy intervention",
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


def _prepend_workstream_priority(
    workstream: str,
    block_name: str,
    priority: int,
) -> None:
    priorities = semantic_blocks.WORKSTREAM_SEMANTIC_PRIORITIES.setdefault(workstream, [])
    existing = [(name, value) for name, value in priorities if name != block_name]
    priorities[:] = [(block_name, priority), *existing]


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
    _extend_semantic_block(
        "food_literacy_agency",
        terms=FOOD_SKILLS_SELF_EFFICACY_TERMS,
        document_terms=FOOD_SKILLS_SELF_EFFICACY_DOCUMENT_TERMS,
    )
    _extend_semantic_block(
        "food_farmacy_programs",
        terms=FOOD_FARMACY_TERMS,
        document_terms=FOOD_FARMACY_DOCUMENT_TERMS,
    )
    _prepend_workstream_priority("busca1", "food_farmacy_programs", 5)
    _prepend_workstream_priority("busca2b", "food_farmacy_programs", 5)
    for block_name in ("equity_access", "food_prescription_programs"):
        _extend_semantic_block(
            block_name,
            terms=SOCIAL_NEEDS_FOOD_ACCESS_TERMS,
            document_terms=SOCIAL_NEEDS_FOOD_ACCESS_DOCUMENT_TERMS,
        )


apply_semantic_extensions()
