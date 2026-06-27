from __future__ import annotations

from nutev.querypacks import semantic_blocks

ADHERENCE_PRECISION_TERMS = [
    "dietary action planning",
    "dietary coping planning",
    "action control",
    "dietary action control",
    "dietary goal setting",
    "dietary problem solving",
    "dietary relapse prevention",
    "dietary lapse management",
    "eating habit formation",
    "habit strength",
    "dietary habit strength",
    "automaticity",
    "dietary automaticity",
    "self-monitoring of diet",
    "self-monitoring of food intake",
    "food intake self-monitoring",
    "diet tracking",
    "food tracking",
    "dietary feedback",
    "nutrition feedback",
    "coping self-efficacy",
    "dietary self-efficacy",
    "weight maintenance behavior",
    "weight maintenance behaviour",
    "maintenance self-efficacy",
    "maintenance intervention",
    "long-term dietary behavior change",
    "long term dietary behavior change",
    "long-term dietary behaviour change",
    "long term dietary behaviour change",
]

ADHERENCE_PRECISION_DOCUMENT_TERMS = [
    "dietary action planning intervention",
    "dietary coping planning intervention",
    "action control intervention",
    "dietary self-monitoring intervention",
    "food intake self-monitoring intervention",
    "diet tracking intervention",
    "food tracking intervention",
    "dietary feedback intervention",
    "habit formation intervention",
    "habit strength intervention",
    "dietary relapse prevention intervention",
    "dietary lapse management intervention",
    "weight maintenance behavior intervention",
    "weight maintenance behaviour intervention",
    "long-term dietary behavior change intervention",
    "long term dietary behavior change intervention",
    "long-term dietary behaviour change intervention",
    "long term dietary behaviour change intervention",
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


def apply_adherence_precision_extensions() -> None:
    for block_name in ("adherence_persistence", "implementation_science"):
        _extend_semantic_block(
            block_name,
            terms=ADHERENCE_PRECISION_TERMS,
            document_terms=ADHERENCE_PRECISION_DOCUMENT_TERMS,
        )


apply_adherence_precision_extensions()
