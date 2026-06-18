from __future__ import annotations

from nutev.querypacks import semantic_blocks

DIETARY_BEHAVIOR_MAINTENANCE_TERMS = [
    "dietary relapse prevention",
    "diet relapse prevention",
    "relapse prevention for weight management",
    "lapse management intervention",
    "dietary lapse management",
    "eating lapse management",
    "weight regain prevention intervention",
    "weight maintenance intervention",
    "dietary maintenance intervention",
    "maintenance of dietary behavior change",
    "maintenance of dietary behaviour change",
    "long-term dietary behavior change",
    "long term dietary behavior change",
    "long-term dietary behaviour change",
    "long term dietary behaviour change",
    "habit-based dietary intervention",
    "habit based dietary intervention",
    "healthy eating habit formation",
    "dietary habit formation",
    "meal planning habit",
    "self-regulation of eating behavior",
    "self-regulation of eating behaviour",
    "dietary coping planning",
    "dietary action planning",
]

DIETARY_BEHAVIOR_MAINTENANCE_DOCUMENT_TERMS = [
    "relapse prevention intervention",
    "dietary relapse prevention intervention",
    "lapse management intervention",
    "weight regain prevention intervention",
    "weight maintenance intervention",
    "dietary maintenance intervention",
    "habit formation intervention",
    "habit-based dietary intervention",
    "habit based dietary intervention",
    "self-regulation intervention",
    "dietary self-regulation intervention",
    "dietary action planning intervention",
    "dietary coping planning intervention",
]


def _extend_unique(existing: list[str], additions: list[str]) -> list[str]:
    seen = {item.lower() for item in existing}
    for item in additions:
        value = str(item).strip()
        if not value:
            continue
        key = value.lower()
        if key in seen:
            continue
        existing.append(value)
        seen.add(key)
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


def apply_behavior_maintenance_extensions() -> None:
    for block_name in (
        "adherence_persistence",
        "implementation_science",
        "lifestyle_nutrition_patterns",
    ):
        _extend_semantic_block(
            block_name,
            terms=DIETARY_BEHAVIOR_MAINTENANCE_TERMS,
            document_terms=DIETARY_BEHAVIOR_MAINTENANCE_DOCUMENT_TERMS,
        )
