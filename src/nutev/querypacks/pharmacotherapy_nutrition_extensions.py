from __future__ import annotations

from nutev.querypacks import semantic_blocks

PHARMACOTHERAPY_NUTRITION_TERMS = [
    "anti-obesity medication nutrition",
    "anti-obesity medication nutrition care",
    "anti-obesity medication dietary counseling",
    "anti-obesity medication lifestyle intervention",
    "obesity pharmacotherapy nutrition",
    "obesity pharmacotherapy nutrition care",
    "obesity pharmacotherapy dietary counseling",
    "obesity pharmacotherapy lifestyle intervention",
    "glp-1 nutrition",
    "glp-1 nutrition care",
    "glp-1 dietary counseling",
    "glp-1 lifestyle intervention",
    "glp-1 receptor agonist nutrition",
    "glp-1 receptor agonist nutrition care",
    "glp-1 receptor agonist dietary counseling",
    "glp-1 receptor agonist lifestyle intervention",
    "incretin therapy nutrition",
    "incretin therapy nutrition care",
    "incretin therapy dietary counseling",
    "incretin therapy lifestyle intervention",
    "semaglutide nutrition",
    "semaglutide nutrition care",
    "semaglutide dietary counseling",
    "semaglutide lifestyle intervention",
    "tirzepatide nutrition",
    "tirzepatide nutrition care",
    "tirzepatide dietary counseling",
    "tirzepatide lifestyle intervention",
    "protein intake during pharmacotherapy",
    "protein intake during weight loss pharmacotherapy",
    "muscle mass preservation during weight loss",
    "lean mass preservation during weight loss",
]

PHARMACOTHERAPY_NUTRITION_DOCUMENT_TERMS = [
    "anti-obesity medication nutrition care",
    "anti-obesity medication dietary counseling",
    "obesity pharmacotherapy nutrition care",
    "obesity pharmacotherapy lifestyle intervention",
    "glp-1 receptor agonist nutrition care",
    "glp-1 receptor agonist dietary counseling",
    "glp-1 receptor agonist lifestyle intervention",
    "incretin therapy nutrition care",
    "semaglutide nutrition care",
    "semaglutide lifestyle intervention",
    "tirzepatide nutrition care",
    "tirzepatide lifestyle intervention",
    "protein intake during weight loss pharmacotherapy",
    "lean mass preservation during weight loss",
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
    block_name: str, priorities: dict[str, int]) -> None:
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
        "pharmacotherapy_nutrition_care",
        terms=PHARMACOTHERAPY_NUTRITION_TERMS,
        document_terms=PHARMACOTHERAPY_NUTRITION_DOCUMENT_TERMS,
    )
    _prioritize_semantic_block(
        "pharmacotherapy_nutrition_care",
        {"busca2a": 5, "busca2b": 5},
    )