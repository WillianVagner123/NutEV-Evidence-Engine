from __future__ import annotations

from nutev.querypacks import semantic_blocks

GROUP_VISIT_CARE_DELIVERY_TERMS = [
    "shared medical appointment",
    "shared medical appointments",
    "shared medical visit",
    "shared medical visits",
    "group medical visit",
    "group medical visits",
    "group visit",
    "group visits",
    "group visit model",
    "group-based care",
    "group based care",
    "group-based lifestyle intervention",
    "group based lifestyle intervention",
    "group lifestyle intervention",
    "group lifestyle interventions",
    "group lifestyle program",
    "group lifestyle programme",
    "group weight management program",
    "group weight management programme",
    "group obesity treatment",
    "group obesity care",
    "group nutrition visit",
    "group nutrition visits",
    "group nutrition counseling",
    "group nutrition counselling",
    "group lifestyle counseling",
    "group lifestyle counselling",
    "group medical nutrition therapy",
    "shared medical appointment nutrition",
    "group diabetes prevention program",
    "group diabetes prevention programme",
    "group-based diabetes prevention program",
    "group based diabetes prevention program",
]

GROUP_VISIT_CARE_DELIVERY_DOCUMENT_TERMS = [
    "shared medical appointment trial",
    "shared medical appointment evaluation",
    "shared medical visit trial",
    "shared medical visit evaluation",
    "group medical visit trial",
    "group medical visit evaluation",
    "group visit intervention",
    "group visit trial",
    "group visit program evaluation",
    "group-based lifestyle intervention trial",
    "group based lifestyle intervention trial",
    "group lifestyle intervention trial",
    "group lifestyle program evaluation",
    "group lifestyle programme evaluation",
    "group weight management trial",
    "group weight management program evaluation",
    "group obesity treatment trial",
    "group nutrition counseling intervention",
    "group nutrition counselling intervention",
    "group medical nutrition therapy intervention",
    "group diabetes prevention program evaluation",
    "group diabetes prevention programme evaluation",
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
    block_name: str, priorities: dict[str, int]) -> None:
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


def apply_group_visit_care_extensions() -> None:
    _extend_semantic_block(
        "group_visit_care_delivery",
        terms=GROUP_VISIT_CARE_DELIVERY_TERMS,
        document_terms=GROUP_VISIT_CARE_DELIVERY_DOCUMENT_TERMS,
    )
    _prioritize_semantic_block(
        "group_visit_care_delivery",
        {"busca2b": 5, "busca2a": 4, "artigo3_framework": 4, "busca1": 3},
    )
