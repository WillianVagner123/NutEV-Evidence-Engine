from __future__ import annotations

from nutev.querypacks import semantic_blocks

ADHERENCE_MAINTENANCE_TERMS = [
    "dietary relapse prevention",
    "relapse prevention for weight management",
    "weight maintenance intervention",
    "weight maintenance interventions",
    "weight loss maintenance intervention",
    "weight loss maintenance interventions",
    "maintenance of behavior change",
    "maintenance of behaviour change",
    "behavior change maintenance",
    "behaviour change maintenance",
    "dietary habit formation",
    "healthy eating habit formation",
    "habit-based dietary intervention",
    "habit based dietary intervention",
    "implementation intentions for diet",
    "implementation intention intervention",
    "action control",
    "coping self-efficacy",
    "dietary self-efficacy",
    "eating self-efficacy",
    "dietary self-management support",
    "long-term dietary adherence",
    "long term dietary adherence",
]

ADHERENCE_MAINTENANCE_DOCUMENT_TERMS = [
    "dietary relapse prevention intervention",
    "weight maintenance intervention trial",
    "weight loss maintenance intervention trial",
    "weight maintenance systematic review",
    "weight regain prevention systematic review",
    "behavior change maintenance trial",
    "behaviour change maintenance trial",
    "habit formation intervention",
    "habit-based dietary intervention",
    "habit based dietary intervention",
    "implementation intention intervention",
    "dietary self-management intervention",
    "long-term dietary adherence intervention",
    "long term dietary adherence intervention",
]

TARGET_BLOCKS = (
    "adherence_persistence",
    "implementation_science",
    "lifestyle_nutrition_patterns",
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


def apply_adherence_maintenance_extensions() -> None:
    for block_name in TARGET_BLOCKS:
        _extend_semantic_block(
            block_name,
            terms=ADHERENCE_MAINTENANCE_TERMS,
            document_terms=ADHERENCE_MAINTENANCE_DOCUMENT_TERMS,
        )
