from __future__ import annotations

from nutev.querypacks import semantic_blocks

DIET_QUALITY_INDEX_TERMS = [
    "diet quality",
    "diet quality index",
    "diet quality indices",
    "diet quality score",
    "diet quality scores",
    "dietary quality index",
    "dietary quality score",
    "dietary quality scores",
    "healthy eating index",
    "healthy eating index 2015",
    "hei-2015",
    "hei 2015",
    "alternate healthy eating index",
    "alternative healthy eating index",
    "ahei",
    "dietary inflammatory index",
    "dii score",
    "empirical dietary inflammatory pattern",
    "empirical dietary index for hyperinsulinemia",
    "empirical dietary inflammatory index",
    "dietary pattern score",
    "dietary pattern scores",
    "dietary adherence score",
    "dietary adherence scores",
    "mediterranean diet score",
    "mediterranean dietary score",
    "dash score",
    "dash diet score",
    "mind diet score",
    "portfolio diet score",
    "plant-based diet index",
    "plant based diet index",
    "healthy plant-based diet index",
    "healthy plant based diet index",
    "healthful plant-based diet index",
    "unhealthy plant-based diet index",
    "provegetarian diet index",
    "pro-vegetarian diet index",
    "healthy diet indicator",
]

DIET_QUALITY_INDEX_DOCUMENT_TERMS = [
    "diet quality guideline",
    "diet quality guidelines",
    "diet quality systematic review",
    "diet quality meta-analysis",
    "diet quality umbrella review",
    "diet quality index validation",
    "diet quality score validation",
    "dietary quality score validation",
    "healthy eating index validation",
    "healthy eating index systematic review",
    "alternate healthy eating index systematic review",
    "alternative healthy eating index systematic review",
    "dietary inflammatory index systematic review",
    "dietary inflammatory index meta-analysis",
    "dietary pattern score validation",
    "dietary adherence score validation",
    "mediterranean diet adherence score",
    "dash adherence score",
    "plant-based diet index validation",
    "plant based diet index validation",
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


def apply_diet_quality_extensions() -> None:
    _extend_semantic_block(
        "diet_quality_indices",
        terms=DIET_QUALITY_INDEX_TERMS,
        document_terms=DIET_QUALITY_INDEX_DOCUMENT_TERMS,
    )
    _prioritize_semantic_block(
        "diet_quality_indices",
        {"busca1": 4, "busca2a": 5, "busca2b": 5, "artigo3_framework": 3},
    )
