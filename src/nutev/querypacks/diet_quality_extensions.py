from __future__ import annotations

from nutev.querypacks import semantic_blocks

DIET_QUALITY_ADHERENCE_TERMS = [
    "diet quality index revised",
    "diet quality index-international",
    "diet quality index international",
    "dqi-r",
    "dqi-i",
    "healthy eating index 2015",
    "hei-2015",
    "healthy eating index 2020",
    "hei-2020",
    "alternate healthy eating index 2010",
    "ahei-2010",
    "healthy diet indicator",
    "healthy diet score",
    "healthy diet scores",
    "dietary guideline adherence",
    "dietary guidelines adherence",
    "food-based dietary guideline adherence",
    "food based dietary guideline adherence",
    "dietary recommendations adherence",
    "dietary recommendation adherence",
    "dietary guideline score",
    "dietary guidelines score",
    "recommended food score",
    "healthy food diversity index",
    "food variety score",
    "diet variety score",
    "dietary diversity score",
    "minimum dietary diversity",
    "nutrient-rich food index",
    "nutrient rich food index",
    "nutriscore",
    "nutri-score",
    "front-of-pack nutrition score",
    "front of pack nutrition score",
    "nova dietary pattern",
    "nova dietary score",
]

DIET_QUALITY_ADHERENCE_DOCUMENT_TERMS = [
    "diet quality index validation",
    "diet quality index-international validation",
    "diet quality index international validation",
    "healthy eating index 2015 validation",
    "healthy eating index 2020 validation",
    "alternate healthy eating index validation",
    "healthy diet indicator validation",
    "dietary guideline adherence score",
    "dietary guidelines adherence score",
    "food-based dietary guideline adherence score",
    "food based dietary guideline adherence score",
    "dietary recommendation adherence score",
    "recommended food score validation",
    "dietary diversity score validation",
    "nutrient-rich food index validation",
    "nutrient rich food index validation",
    "front-of-pack nutrition score validation",
    "front of pack nutrition score validation",
]

DIET_QUALITY_BLOCK_PRIORITIES = {
    "busca1": 4,
    "busca2a": 4,
    "busca2b": 5,
    "artigo3_framework": 4,
}


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


def _prioritize_block(block_name: str) -> None:
    for workstream, priority in DIET_QUALITY_BLOCK_PRIORITIES.items():
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
        "diet_quality_adherence",
        terms=DIET_QUALITY_ADHERENCE_TERMS,
        document_terms=DIET_QUALITY_ADHERENCE_DOCUMENT_TERMS,
    )
    _prioritize_block("diet_quality_adherence")
    for block_name in ("adherence_persistence", "lifestyle_nutrition_patterns"):
        _extend_semantic_block(
            block_name,
            terms=DIET_QUALITY_ADHERENCE_TERMS,
            document_terms=DIET_QUALITY_ADHERENCE_DOCUMENT_TERMS,
        )


apply_diet_quality_extensions()
