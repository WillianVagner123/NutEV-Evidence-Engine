from __future__ import annotations

from nutev.querypacks import semantic_blocks

PROCESSING_QUALITY_TERMS = [
    "highly processed food",
    "highly processed foods",
    "industrialized food",
    "industrialized foods",
    "industrialised food",
    "industrialised foods",
    "nova group 4",
    "nova 4",
    "nova category 4",
    "ultra-processed dietary pattern",
    "ultra processed dietary pattern",
    "ultra-processed diet",
    "ultra processed diet",
    "processed food intake",
    "processed food consumption",
    "food processing level",
    "food processing classification",
    "minimally processed diet",
    "whole food dietary pattern",
    "whole-food dietary pattern",
]

PROCESSING_QUALITY_DOCUMENT_TERMS = [
    "ultra-processed food guideline",
    "ultra processed food guideline",
    "ultra-processed food guidance",
    "ultra processed food guidance",
    "ultra-processed food consensus",
    "ultra processed food consensus",
    "ultra-processed food systematic review",
    "ultra processed food systematic review",
    "ultra-processed food umbrella review",
    "ultra processed food umbrella review",
    "ultra-processed food meta-analysis",
    "ultra processed food meta-analysis",
    "nova classification systematic review",
    "nova classification umbrella review",
    "nova classification meta-analysis",
]

_TARGET_BLOCKS = (
    "diet_processing_quality",
    "lifestyle_nutrition_patterns",
    "cardiometabolic_precision",
)


def _extend_unique(existing: list[str], additions: list[str]) -> list[str]:
    seen = {item.lower() for item in existing}
    for item in additions:
        value = item.strip()
        if not value or value.lower() in seen:
            continue
        existing.append(value)
        seen.add(value.lower())
    return existing


def _extend_semantic_block(block_name: str) -> None:
    block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS.setdefault(
        block_name,
        {"terms": [], "document_terms": []},
    )
    block["terms"] = _extend_unique(
        block.setdefault("terms", []),
        PROCESSING_QUALITY_TERMS,
    )
    block["document_terms"] = _extend_unique(
        block.setdefault("document_terms", []),
        PROCESSING_QUALITY_DOCUMENT_TERMS,
    )


def _ensure_priority(workstream: str, block_name: str, priority: int) -> None:
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


def apply_processing_quality_extensions() -> None:
    for block_name in _TARGET_BLOCKS:
        _extend_semantic_block(block_name)
    _ensure_priority("busca1", "diet_processing_quality", 4)
    _ensure_priority("busca2a", "diet_processing_quality", 5)
    _ensure_priority("busca2b", "diet_processing_quality", 5)
