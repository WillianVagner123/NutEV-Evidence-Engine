from __future__ import annotations

from nutev.querypacks import semantic_blocks

GROUP_LIFESTYLE_NUTRITION_DELIVERY_TERMS = [
    "group-based lifestyle intervention",
    "group based lifestyle intervention",
    "group lifestyle intervention",
    "group lifestyle program",
    "group lifestyle programme",
    "group-based weight management",
    "group based weight management",
    "group weight management program",
    "group weight management programme",
    "group-based obesity treatment",
    "group based obesity treatment",
    "group obesity intervention",
    "group diabetes prevention program",
    "group diabetes prevention programme",
    "group diabetes prevention intervention",
    "group type 2 diabetes lifestyle intervention",
    "group cardiometabolic lifestyle intervention",
    "group nutrition counseling",
    "group nutrition counselling",
    "group dietary counseling",
    "group dietary counselling",
    "group medical nutrition therapy",
    "group nutrition education",
    "group visits nutrition",
    "group visit nutrition",
    "group visits obesity",
    "group visit obesity",
    "group visits diabetes",
    "group visit diabetes",
    "shared medical appointment nutrition",
    "shared medical appointments nutrition",
    "shared medical appointment obesity",
    "shared medical appointments obesity",
    "shared medical appointment diabetes",
    "shared medical appointments diabetes",
    "shared medical appointment weight management",
    "shared medical appointments weight management",
    "shared medical appointment lifestyle",
    "shared medical appointments lifestyle",
    "shared medical appointment cardiometabolic",
    "shared medical appointments cardiometabolic",
    "group medical visit nutrition",
    "group medical visits nutrition",
    "group medical visit obesity",
    "group medical visits obesity",
    "group medical visit diabetes",
    "group medical visits diabetes",
    "group medical visit lifestyle",
    "group medical visits lifestyle",
]

GROUP_LIFESTYLE_NUTRITION_DELIVERY_DOCUMENT_TERMS = [
    "group-based lifestyle intervention trial",
    "group based lifestyle intervention trial",
    "group lifestyle intervention trial",
    "group weight management trial",
    "group obesity intervention trial",
    "group diabetes prevention intervention trial",
    "group nutrition counseling intervention",
    "group nutrition counselling intervention",
    "group dietary counseling intervention",
    "group dietary counselling intervention",
    "group medical nutrition therapy intervention",
    "group nutrition education intervention",
    "shared medical appointment trial",
    "shared medical appointments trial",
    "shared medical appointment implementation study",
    "shared medical appointments implementation study",
    "shared medical appointment program evaluation",
    "shared medical appointments program evaluation",
    "group medical visit trial",
    "group medical visits trial",
    "group medical visit implementation study",
    "group medical visits implementation study",
    "group medical visit program evaluation",
    "group medical visits program evaluation",
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
    terms: list[str] | None = None,
    document_terms: list[str] | None = None,
) -> None:
    block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS.setdefault(
        block_name,
        {"terms": [], "document_terms": []},
    )
    if terms:
        block["terms"] = _extend_unique(block.setdefault("terms", []), terms)
    if document_terms:
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


def apply_group_delivery_extensions() -> None:
    _extend_semantic_block(
        "group_lifestyle_nutrition_delivery",
        terms=GROUP_LIFESTYLE_NUTRITION_DELIVERY_TERMS,
        document_terms=GROUP_LIFESTYLE_NUTRITION_DELIVERY_DOCUMENT_TERMS,
    )
    _prioritize_semantic_block(
        "group_lifestyle_nutrition_delivery",
        {
            "busca2b": 5,
            "busca2a": 4,
            "artigo3_framework": 4,
            "busca1": 3,
        },
    )
    for block_name in (
        "implementation_science",
        "nutrition_care_delivery",
        "adherence_persistence",
        "lifestyle_nutrition_patterns",
    ):
        _extend_semantic_block(
            block_name,
            terms=GROUP_LIFESTYLE_NUTRITION_DELIVERY_TERMS,
            document_terms=GROUP_LIFESTYLE_NUTRITION_DELIVERY_DOCUMENT_TERMS,
        )
