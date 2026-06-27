from __future__ import annotations

from nutev.querypacks import semantic_blocks

CARBOHYDRATE_FIBER_QUALITY_TERMS = [
    "carbohydrate quality",
    "carbohydrate quality for cardiometabolic risk",
    "carbohydrate quality for obesity",
    "carbohydrate quality for type 2 diabetes",
    "dietary carbohydrate quality",
    "carbohydrate quality index",
    "carbohydrate quality score",
    "carbohydrate quality metrics",
    "dietary fiber",
    "dietary fibre",
    "dietary fiber intake",
    "dietary fibre intake",
    "fiber intake",
    "fibre intake",
    "fiber density",
    "fibre density",
    "dietary fiber cardiometabolic risk",
    "dietary fibre cardiometabolic risk",
    "dietary fiber for type 2 diabetes",
    "dietary fibre for type 2 diabetes",
    "high-fiber diet",
    "high fibre diet",
    "high-fiber dietary pattern",
    "high fibre dietary pattern",
    "whole grain",
    "whole grains",
    "whole grain intake",
    "whole-grain intake",
    "whole grain diet",
    "whole-grain diet",
    "whole grain dietary pattern",
    "whole-grain dietary pattern",
    "whole grain cardiometabolic risk",
    "whole-grain cardiometabolic risk",
    "whole grain for type 2 diabetes",
    "whole-grain for type 2 diabetes",
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
    "glycemic index cardiometabolic risk",
    "glycaemic index cardiometabolic risk",
    "glycemic load cardiometabolic risk",
    "glycaemic load cardiometabolic risk",
    "postprandial glycemia",
    "postprandial glycaemia",
    "postprandial glucose",
    "low glycemic index diet",
    "low glycaemic index diet",
    "low glycemic load diet",
    "low glycaemic load diet",
]

CARBOHYDRATE_FIBER_QUALITY_DOCUMENT_TERMS = [
    "carbohydrate quality guideline",
    "carbohydrate quality systematic review",
    "carbohydrate quality meta-analysis",
    "carbohydrate quality intervention trial",
    "carbohydrate quality cardiometabolic systematic review",
    "dietary fiber guideline",
    "dietary fibre guideline",
    "dietary fiber systematic review",
    "dietary fibre systematic review",
    "dietary fiber meta-analysis",
    "dietary fibre meta-analysis",
    "dietary fiber intervention trial",
    "dietary fibre intervention trial",
    "dietary fiber cardiometabolic intervention trial",
    "dietary fibre cardiometabolic intervention trial",
    "whole grain guideline",
    "whole grain systematic review",
    "whole grain meta-analysis",
    "whole grain intervention trial",
    "whole grain cardiometabolic systematic review",
    "whole grain cardiometabolic intervention trial",
    "glycemic index systematic review",
    "glycaemic index systematic review",
    "glycemic load systematic review",
    "glycaemic load systematic review",
    "glycemic index cardiometabolic systematic review",
    "glycaemic index cardiometabolic systematic review",
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
