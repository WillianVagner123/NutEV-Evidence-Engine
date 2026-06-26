from __future__ import annotations

from nutev.querypacks import semantic_blocks

ANTI_OBESITY_PHARMACOTHERAPY_NUTRITION_TERMS = [
    "anti-obesity medication nutrition",
    "anti-obesity medication dietary counseling",
    "anti-obesity medication dietary counselling",
    "anti-obesity medication lifestyle intervention",
    "anti-obesity medication dietary adherence",
    "obesity pharmacotherapy nutrition care",
    "obesity pharmacotherapy dietary counseling",
    "obesity pharmacotherapy dietary counselling",
    "obesity pharmacotherapy lifestyle intervention",
    "obesity pharmacotherapy dietary adherence",
    "glp-1 nutrition",
    "glp-1 dietary counseling",
    "glp-1 dietary counselling",
    "glp-1 lifestyle intervention",
    "glp-1 dietary adherence",
    "glp-1 weight maintenance",
    "glp-1 receptor agonist nutrition",
    "glp-1 receptor agonist dietary counseling",
    "glp-1 receptor agonist dietary counselling",
    "glp-1 receptor agonist lifestyle intervention",
    "incretin therapy nutrition care",
    "incretin therapy dietary counseling",
    "incretin therapy dietary counselling",
    "incretin therapy lifestyle intervention",
    "semaglutide nutrition",
    "semaglutide dietary counseling",
    "semaglutide dietary counselling",
    "tirzepatide nutrition",
    "tirzepatide dietary counseling",
    "tirzepatide dietary counselling",
    "lean mass preservation",
    "muscle mass preservation",
    "protein intake during weight loss",
    "diet quality during pharmacotherapy",
    "weight regain after medication discontinuation",
]

ANTI_OBESITY_PHARMACOTHERAPY_DOCUMENT_TERMS = [
    "anti-obesity medication nutrition guidance",
    "anti-obesity medication nutrition guideline",
    "anti-obesity medication lifestyle intervention trial",
    "anti-obesity medication dietary adherence study",
    "obesity pharmacotherapy nutrition care guideline",
    "obesity pharmacotherapy lifestyle intervention trial",
    "glp-1 nutrition guidance",
    "glp-1 dietary counseling guideline",
    "glp-1 dietary counselling guideline",
    "glp-1 lifestyle intervention trial",
    "glp-1 dietary adherence study",
    "glp-1 weight maintenance study",
    "glp-1 receptor agonist nutrition guidance",
    "incretin therapy nutrition guidance",
    "semaglutide nutrition counseling",
    "semaglutide dietary counseling",
    "semaglutide dietary counselling",
    "tirzepatide nutrition counseling",
    "tirzepatide dietary counseling",
    "tirzepatide dietary counselling",
    "lean mass preservation trial",
    "muscle mass preservation trial",
    "protein intake during weight loss trial",
    "weight regain after medication discontinuation study",
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


def apply_glp1_nutrition_extensions() -> None:
    for block_name in (
        "cardiometabolic_precision",
        "lifestyle_nutrition_patterns",
        "adherence_persistence",
        "nutrition_care_delivery",
    ):
        _extend_semantic_block(
            block_name,
            terms=ANTI_OBESITY_PHARMACOTHERAPY_NUTRITION_TERMS,
            document_terms=ANTI_OBESITY_PHARMACOTHERAPY_DOCUMENT_TERMS,
        )
