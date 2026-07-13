from __future__ import annotations

from nutev.querypacks import semantic_blocks

GLP1_NUTRITION_TERMS = [
    "anti-obesity medication nutrition",
    "anti-obesity medication dietary counseling",
    "anti-obesity medication dietary counselling",
    "anti-obesity medication nutrition care",
    "anti-obesity medication medical nutrition therapy",
    "obesity pharmacotherapy nutrition care",
    "obesity pharmacotherapy dietary counseling",
    "obesity pharmacotherapy dietary counselling",
    "obesity pharmacotherapy nutrition intervention",
    "obesity pharmacotherapy dietary adherence",
    "glp-1 nutrition",
    "glp-1 dietary counseling",
    "glp-1 dietary counselling",
    "glp-1 nutrition care",
    "glp-1 nutrition therapy",
    "glp-1 medical nutrition therapy",
    "glp-1 receptor agonist nutrition",
    "glp-1 receptor agonist dietary counseling",
    "glp-1 receptor agonist dietary counselling",
    "glp-1 receptor agonist nutrition care",
    "glp-1 receptor agonist medical nutrition therapy",
    "semaglutide nutrition",
    "semaglutide dietary counseling",
    "semaglutide dietary counselling",
    "semaglutide nutrition care",
    "tirzepatide nutrition",
    "tirzepatide dietary counseling",
    "tirzepatide dietary counselling",
    "tirzepatide nutrition care",
    "incretin therapy nutrition care",
    "incretin therapy dietary counseling",
    "incretin therapy dietary counselling",
    "incretin therapy medical nutrition therapy",
    "muscle preservation during weight loss",
    "lean mass preservation during weight loss",
    "protein intake during weight loss",
    "dietary protein during weight loss",
]

GLP1_NUTRITION_DOCUMENT_TERMS = [
    "anti-obesity medication nutrition guideline",
    "anti-obesity medication nutrition consensus",
    "anti-obesity medication dietary counseling guideline",
    "obesity pharmacotherapy nutrition guideline",
    "obesity pharmacotherapy nutrition consensus",
    "obesity pharmacotherapy dietary counseling guideline",
    "glp-1 nutrition guideline",
    "glp-1 nutrition consensus",
    "glp-1 dietary counseling guideline",
    "glp-1 receptor agonist nutrition guideline",
    "glp-1 receptor agonist nutrition consensus",
    "glp-1 receptor agonist dietary counseling guideline",
    "semaglutide nutrition guidance",
    "semaglutide dietary counseling guidance",
    "tirzepatide nutrition guidance",
    "tirzepatide dietary counseling guidance",
    "incretin therapy nutrition guideline",
    "incretin therapy nutrition consensus",
    "incretin therapy dietary counseling guideline",
    "muscle preservation during weight loss guideline",
    "lean mass preservation during weight loss guideline",
    "protein intake during weight loss guideline",
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


def _prioritize_semantic_block(block_name: str, priorities: dict[str, int]) -> None:
    for workstream, priority in priorities.items():
        existing = [
            (name, value)
            for name, value in semantic_blocks.WORKSTREAM_SEMANTIC_PRIORITIES.get(
                workstream,
                [],
            )
            if name != block_name
        ]
        semantic_blocks.WORKSTREAM_SEMANTIC_PRIORITIES[workstream] = [
            (block_name, priority),
            *existing,
        ]


def apply_glp1_nutrition_extensions() -> None:
    _extend_semantic_block(
        "glp1_nutrition_care",
        terms=GLP1_NUTRITION_TERMS,
        document_terms=GLP1_NUTRITION_DOCUMENT_TERMS,
    )
    _prioritize_semantic_block(
        "glp1_nutrition_care",
        {"busca2a": 5, "busca2b": 5},
    )
