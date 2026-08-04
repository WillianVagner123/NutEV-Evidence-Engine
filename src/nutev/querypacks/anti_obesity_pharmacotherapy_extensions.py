from __future__ import annotations

from nutev.querypacks import semantic_blocks

ANTI_OBESITY_PHARMACOTHERAPY_NUTRITION_TERMS = [
    "anti-obesity medication nutrition",
    "anti-obesity medication dietary counseling",
    "anti-obesity medication nutrition care",
    "anti-obesity pharmacotherapy nutrition",
    "anti-obesity pharmacotherapy dietary counseling",
    "obesity pharmacotherapy nutrition care",
    "obesity pharmacotherapy dietary counseling",
    "glp-1 nutrition",
    "glp-1 dietary counseling",
    "glp-1 nutrition care",
    "glp-1 receptor agonist nutrition",
    "glp-1 receptor agonist dietary counseling",
    "glp-1 receptor agonist nutrition care",
    "incretin therapy nutrition care",
    "incretin therapy dietary counseling",
    "semaglutide nutrition",
    "semaglutide dietary counseling",
    "tirzepatide nutrition",
    "tirzepatide dietary counseling",
    "lean mass preservation",
    "fat-free mass preservation",
    "fat free mass preservation",
    "muscle preservation",
    "protein adequacy",
    "protein distribution",
    "dietary protein adequacy",
    "nutrition care during weight loss pharmacotherapy",
]

ANTI_OBESITY_PHARMACOTHERAPY_DOCUMENT_TERMS = [
    "anti-obesity medication nutrition guidance",
    "anti-obesity medication dietary counseling guidance",
    "anti-obesity pharmacotherapy nutrition guideline",
    "obesity pharmacotherapy nutrition guidance",
    "glp-1 nutrition guidance",
    "glp-1 dietary counseling guidance",
    "glp-1 receptor agonist nutrition guidance",
    "incretin therapy nutrition guidance",
    "semaglutide nutrition guidance",
    "tirzepatide nutrition guidance",
    "lean mass preservation guideline",
    "lean mass preservation systematic review",
    "protein adequacy weight loss pharmacotherapy",
    "dietary protein anti-obesity medication",
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


def apply_anti_obesity_pharmacotherapy_extensions() -> None:
    _extend_semantic_block(
        "anti_obesity_pharmacotherapy_nutrition",
        terms=ANTI_OBESITY_PHARMACOTHERAPY_NUTRITION_TERMS,
        document_terms=ANTI_OBESITY_PHARMACOTHERAPY_DOCUMENT_TERMS,
    )
    _prioritize_semantic_block(
        "anti_obesity_pharmacotherapy_nutrition",
        {"busca2a": 5, "busca2b": 5, "busca1": 3},
    )
