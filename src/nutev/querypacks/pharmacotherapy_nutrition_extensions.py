from __future__ import annotations

from nutev.querypacks import semantic_blocks

PHARMACOTHERAPY_NUTRITION_TERMS = [
    "anti-obesity medication nutrition",
    "anti-obesity medication dietary counseling",
    "anti-obesity medication dietary counselling",
    "anti-obesity medication nutrition care",
    "anti-obesity medication lifestyle intervention",
    "anti-obesity medication dietary adherence",
    "anti-obesity medication weight maintenance",
    "obesity pharmacotherapy nutrition",
    "obesity pharmacotherapy nutrition care",
    "obesity pharmacotherapy dietary counseling",
    "obesity pharmacotherapy dietary counselling",
    "obesity pharmacotherapy lifestyle intervention",
    "obesity pharmacotherapy dietary adherence",
    "obesity pharmacotherapy weight maintenance",
    "glp-1 nutrition",
    "glp-1 nutrition care",
    "glp-1 dietary counseling",
    "glp-1 dietary counselling",
    "glp-1 dietary adherence",
    "glp-1 weight maintenance",
    "glp-1 receptor agonist nutrition",
    "glp-1 receptor agonist nutrition care",
    "glp-1 receptor agonist dietary counseling",
    "glp-1 receptor agonist dietary counselling",
    "glp-1 receptor agonist lifestyle intervention",
    "glp-1 receptor agonist dietary adherence",
    "glp-1 receptor agonist weight maintenance",
    "semaglutide nutrition care",
    "semaglutide dietary counseling",
    "semaglutide dietary counselling",
    "semaglutide lifestyle intervention",
    "tirzepatide nutrition care",
    "tirzepatide dietary counseling",
    "tirzepatide dietary counselling",
    "tirzepatide lifestyle intervention",
    "incretin therapy nutrition",
    "incretin therapy nutrition care",
    "incretin therapy dietary counseling",
    "incretin therapy dietary counselling",
    "incretin therapy lifestyle intervention",
    "incretin therapy dietary adherence",
    "incretin therapy weight maintenance",
    "post-pharmacotherapy weight maintenance",
    "post pharmacotherapy weight maintenance",
    "post-glp-1 weight maintenance",
    "post glp-1 weight maintenance",
    "post-incretin weight maintenance",
    "post incretin weight maintenance",
    "weight regain after anti-obesity medication",
    "weight regain after glp-1",
    "weight regain after incretin therapy",
]

PHARMACOTHERAPY_NUTRITION_DOCUMENT_TERMS = [
    "anti-obesity medication nutrition guidance",
    "anti-obesity medication dietary counseling guidance",
    "anti-obesity medication nutrition care guideline",
    "anti-obesity medication lifestyle intervention trial",
    "anti-obesity medication dietary adherence study",
    "anti-obesity medication weight maintenance trial",
    "obesity pharmacotherapy nutrition guidance",
    "obesity pharmacotherapy nutrition care guideline",
    "obesity pharmacotherapy lifestyle intervention trial",
    "obesity pharmacotherapy dietary adherence study",
    "glp-1 nutrition guidance",
    "glp-1 nutrition care guideline",
    "glp-1 dietary counseling guidance",
    "glp-1 lifestyle intervention trial",
    "glp-1 dietary adherence study",
    "glp-1 weight maintenance trial",
    "glp-1 receptor agonist nutrition guidance",
    "glp-1 receptor agonist nutrition care guideline",
    "glp-1 receptor agonist lifestyle intervention trial",
    "incretin therapy nutrition guidance",
    "incretin therapy nutrition care guideline",
    "incretin therapy lifestyle intervention trial",
    "incretin therapy dietary adherence study",
    "post-glp-1 weight maintenance trial",
    "post-incretin weight maintenance trial",
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


def _prioritize_semantic_block(
    block_name: str,
    priorities: dict[str, int],
) -> None:
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


def apply_pharmacotherapy_nutrition_extensions() -> None:
    _extend_semantic_block(
        "pharmacotherapy_nutrition_support",
        terms=PHARMACOTHERAPY_NUTRITION_TERMS,
        document_terms=PHARMACOTHERAPY_NUTRITION_DOCUMENT_TERMS,
    )
    _prioritize_semantic_block(
        "pharmacotherapy_nutrition_support",
        {"busca2a": 4, "busca2b": 5},
    )
    for block_name in (
        "adherence_persistence",
        "implementation_science",
        "lifestyle_nutrition_patterns",
    ):
        _extend_semantic_block(
            block_name,
            terms=PHARMACOTHERAPY_NUTRITION_TERMS,
            document_terms=PHARMACOTHERAPY_NUTRITION_DOCUMENT_TERMS,
        )
