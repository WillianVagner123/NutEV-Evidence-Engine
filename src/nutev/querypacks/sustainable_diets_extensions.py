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
    "sustainable diet",
    "sustainable diets",
    "planetary health diet",
    "planetary health diets",
    "eat-lancet diet",
    "eat-lancet dietary pattern",
    "eat-lancet reference diet",
    "planetary health dietary pattern",
    "plant-forward diet",
    "plant forward diet",
    "plant-forward dietary pattern",
    "plant forward dietary pattern",
]

SUSTAINABLE_HEALTHY_DIET_DOCUMENT_TERMS = [
    "sustainable healthy diet guideline",
    "sustainable healthy diets guideline",
    "sustainable healthy diet guidance",
    "sustainable healthy diets guidance",
    "sustainable healthy diet systematic review",
    "sustainable healthy diets systematic review",
    "sustainable healthy diet meta-analysis",
    "healthy sustainable diet systematic review",
    "healthy and sustainable diets systematic review",
    "sustainable dietary pattern systematic review",
    "sustainable dietary patterns systematic review",
    "planetary health diet guideline",
    "planetary health diet systematic review",
    "eat-lancet diet systematic review",
    "eat-lancet reference diet systematic review",
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


def apply_sustainable_diets_extensions() -> None:
    _extend_semantic_block(
        "sustainable_healthy_diets",
        terms=SUSTAINABLE_HEALTHY_DIET_TERMS,
        document_terms=SUSTAINABLE_HEALTHY_DIET_DOCUMENT_TERMS,
    )
    _prioritize_semantic_block(
        "sustainable_healthy_diets",
        {"busca1": 4, "busca2a": 4, "busca2b": 5},
    )
