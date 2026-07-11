from __future__ import annotations

from nutev.querypacks import semantic_blocks

SUSTAINABLE_HEALTHY_DIET_TERMS = [
    "sustainable healthy diet",
    "sustainable healthy diets",
    "healthy sustainable diet",
    "healthy sustainable diets",
    "healthy and sustainable diet",
    "healthy and sustainable diets",
    "sustainable dietary pattern",
    "sustainable dietary patterns",
    "sustainable food-based dietary guideline",
    "sustainable food based dietary guideline",
    "sustainable dietary guideline",
    "sustainable dietary guidelines",
    "planetary health diet",
    "planetary diet",
    "eat-lancet",
    "eat lancet",
    "planetary health diet index",
    "planetary health diet score",
    "eat-lancet diet score",
    "eat lancet diet score",
    "planetary health diet adherence",
    "eat-lancet adherence",
    "eat lancet adherence",
    "sustainable diet adherence",
    "sustainable healthy eating",
]

SUSTAINABLE_HEALTHY_DIET_DOCUMENT_TERMS = [
    "sustainable healthy diet guideline",
    "sustainable healthy diets guideline",
    "sustainable dietary guideline",
    "sustainable dietary guidelines",
    "sustainable food-based dietary guideline",
    "sustainable food based dietary guideline",
    "planetary health diet guideline",
    "eat-lancet guideline",
    "eat lancet guideline",
    "sustainable healthy diet consensus",
    "sustainable dietary patterns consensus",
    "planetary health diet consensus",
    "eat-lancet consensus",
    "eat lancet consensus",
    "sustainable healthy diet systematic review",
    "sustainable dietary patterns systematic review",
    "planetary health diet systematic review",
    "eat-lancet systematic review",
    "eat lancet systematic review",
    "sustainable healthy diet meta-analysis",
    "sustainable dietary patterns meta-analysis",
    "planetary health diet meta-analysis",
    "eat-lancet meta-analysis",
    "eat lancet meta-analysis",
    "planetary health diet adherence score",
    "eat-lancet diet score validation",
    "eat lancet diet score validation",
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


def apply_sustainable_diet_extensions() -> None:
    _extend_semantic_block(
        "sustainable_healthy_diets",
        terms=SUSTAINABLE_HEALTHY_DIET_TERMS,
        document_terms=SUSTAINABLE_HEALTHY_DIET_DOCUMENT_TERMS,
    )
    for block_name in (
        "lifestyle_nutrition_patterns",
        "cardiometabolic_precision",
        "adherence_persistence",
        "evidence_synthesis",
    ):
        _extend_semantic_block(
            block_name,
            terms=SUSTAINABLE_HEALTHY_DIET_TERMS,
            document_terms=SUSTAINABLE_HEALTHY_DIET_DOCUMENT_TERMS,
        )
    _prioritize_semantic_block(
        "sustainable_healthy_diets",
        {"busca1": 4, "busca2a": 4, "busca2b": 4, "artigo3_framework": 4},
    )
