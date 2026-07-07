from __future__ import annotations

from nutev.querypacks import semantic_blocks

GROUP_VISIT_NUTRITION_TERMS = [
    "shared medical appointment nutrition",
    "shared medical appointments nutrition",
    "shared medical appointment diabetes",
    "shared medical appointments diabetes",
    "shared medical appointment obesity",
    "shared medical appointments obesity",
    "shared medical appointment weight management",
    "group medical visit nutrition",
    "group medical visits nutrition",
    "group medical visit diabetes",
    "group medical visits diabetes",
    "group medical visit obesity",
    "group medical visits obesity",
    "group medical visit weight management",
    "lifestyle medicine group visit",
    "lifestyle medicine group visits",
    "lifestyle medicine shared medical appointment",
    "group-based nutrition intervention",
    "group based nutrition intervention",
    "group-based dietary intervention",
    "group based dietary intervention",
    "group lifestyle intervention diabetes",
    "group lifestyle intervention obesity",
]

GROUP_VISIT_NUTRITION_DOCUMENT_TERMS = [
    "shared medical appointment trial",
    "shared medical appointment program evaluation",
    "shared medical appointment programme evaluation",
    "shared medical appointment implementation study",
    "group medical visit trial",
    "group medical visit program evaluation",
    "group medical visit programme evaluation",
    "group medical visit implementation study",
    "group-based nutrition intervention trial",
    "group based nutrition intervention trial",
    "group-based lifestyle intervention trial",
    "group based lifestyle intervention trial",
    "group lifestyle intervention systematic review",
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


def apply_group_visit_extensions() -> None:
    for block_name in (
        "implementation_science",
        "adherence_persistence",
        "cardiometabolic_precision",
        "lifestyle_nutrition_patterns",
    ):
        _extend_semantic_block(
            block_name,
            terms=GROUP_VISIT_NUTRITION_TERMS,
            document_terms=GROUP_VISIT_NUTRITION_DOCUMENT_TERMS,
        )
