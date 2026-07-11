from __future__ import annotations

from nutev.querypacks import semantic_blocks


DIETARY_ADHERENCE_SUPPORT_TERMS = [
    "dietary self-monitoring",
    "dietary self monitoring",
    "food self-monitoring",
    "food self monitoring",
    "meal self-monitoring",
    "meal self monitoring",
    "diet tracking",
    "food tracking",
    "meal tracking",
    "dietary goal setting",
    "nutrition goal setting",
    "healthy eating goals",
    "dietary action planning",
    "nutrition action planning",
    "dietary coping planning",
    "nutrition coping planning",
    "dietary problem solving",
    "nutrition problem solving",
    "relapse prevention for diet",
    "lapse management for diet",
    "dietary habit formation",
    "healthy eating habit formation",
    "dietary self-regulation",
    "dietary self regulation",
    "eating self-regulation",
    "eating self regulation",
    "self-regulation of eating",
    "self regulation of eating",
    "dietary self-management support",
    "dietary self management support",
    "nutrition self-management support",
    "nutrition self management support",
    "dietary accountability",
    "nutrition accountability",
    "dietary coaching",
    "nutrition coaching",
    "healthy eating coaching",
    "lifestyle coaching for diet",
    "maintenance of dietary change",
    "dietary maintenance",
    "long-term dietary adherence",
    "long term dietary adherence",
]


DIETARY_ADHERENCE_SUPPORT_DOCUMENT_TERMS = [
    "dietary self-monitoring intervention",
    "dietary self monitoring intervention",
    "food self-monitoring intervention",
    "food self monitoring intervention",
    "diet tracking intervention",
    "food tracking intervention",
    "dietary goal setting intervention",
    "nutrition goal setting intervention",
    "dietary action planning intervention",
    "nutrition action planning intervention",
    "dietary coping planning intervention",
    "nutrition coping planning intervention",
    "dietary problem solving intervention",
    "nutrition problem solving intervention",
    "dietary self-regulation intervention",
    "dietary self regulation intervention",
    "eating self-regulation intervention",
    "eating self regulation intervention",
    "dietary self-management support intervention",
    "dietary self management support intervention",
    "nutrition self-management support intervention",
    "nutrition self management support intervention",
    "dietary coaching intervention",
    "nutrition coaching intervention",
    "healthy eating coaching intervention",
    "dietary adherence support intervention",
    "dietary adherence support trial",
    "dietary adherence support systematic review",
    "maintenance of dietary change intervention",
    "long-term dietary adherence intervention",
    "long term dietary adherence intervention",
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


def apply_adherence_support_extensions() -> None:
    for block_name in (
        "adherence_persistence",
        "implementation_science",
        "food_literacy_agency",
    ):
        _extend_semantic_block(
            block_name,
            terms=DIETARY_ADHERENCE_SUPPORT_TERMS,
            document_terms=DIETARY_ADHERENCE_SUPPORT_DOCUMENT_TERMS,
        )


apply_adherence_support_extensions()
