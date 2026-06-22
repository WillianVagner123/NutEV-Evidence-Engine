from __future__ import annotations

from nutev.querypacks import semantic_blocks

CARBOHYDRATE_FIBER_QUALITY_TERMS = [
    "carbohydrate quality",
    "carbohydrate quality for cardiometabolic risk",
    "carbohydrate quality for obesity",
    "carbohydrate quality for type 2 diabetes",
    "dietary carbohydrate quality",
    "dietary fiber",
    "dietary fibre",
    "fiber intake",
    "fibre intake",
    "high-fiber diet",
    "high fibre diet",
    "whole grain",
    "whole grains",
    "whole grain intake",
    "whole-grain intake",
    "whole grain diet",
    "whole-grain diet",
    "whole grain dietary pattern",
    "whole-grain dietary pattern",
    "refined grain",
    "refined grains",
    "refined grain intake",
    "added sugar",
    "added sugars",
    "free sugars",
    "sugar-sweetened beverage",
    "sugar sweetened beverage",
    "sugar-sweetened beverages",
    "sugar sweetened beverages",
    "glycemic index",
    "glycaemic index",
    "glycemic load",
    "glycaemic load",
    "low glycemic index diet",
    "low glycaemic index diet",
    "low glycemic load diet",
    "low glycaemic load diet",
]

CARBOHYDRATE_FIBER_QUALITY_DOCUMENT_TERMS = [
    "carbohydrate quality guideline",
    "carbohydrate quality systematic review",
    "carbohydrate quality meta-analysis",
    "dietary fiber guideline",
    "dietary fibre guideline",
    "dietary fiber systematic review",
    "dietary fibre systematic review",
    "dietary fiber meta-analysis",
    "dietary fibre meta-analysis",
    "dietary fiber intervention trial",
    "dietary fibre intervention trial",
    "whole grain guideline",
    "whole grain systematic review",
    "whole grain meta-analysis",
    "whole grain intervention trial",
    "glycemic index systematic review",
    "glycaemic index systematic review",
    "glycemic load systematic review",
    "glycaemic load systematic review",
    "low glycemic index diet trial",
    "low glycaemic index diet trial",
    "sugar-sweetened beverage guideline",
    "sugar sweetened beverage guideline",
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


def apply_carbohydrate_quality_extensions() -> None:
    _extend_semantic_block(
        "carbohydrate_fiber_quality",
        terms=CARBOHYDRATE_FIBER_QUALITY_TERMS,
        document_terms=CARBOHYDRATE_FIBER_QUALITY_DOCUMENT_TERMS,
    )
    _prioritize_semantic_block(
        "carbohydrate_fiber_quality",
        {"busca1": 4, "busca2a": 5, "busca2b": 5},
    )
