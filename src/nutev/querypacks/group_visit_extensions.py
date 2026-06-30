from __future__ import annotations

from nutev.querypacks import semantic_blocks

GROUP_VISIT_NUTRITION_CARE_TERMS = [
    "group medical visit",
    "group medical visits",
    "shared medical appointment",
    "shared medical appointments",
    "shared medical visit",
    "shared medical visits",
    "group visit",
    "group visits",
    "group lifestyle intervention",
    "group-based lifestyle intervention",
    "group based lifestyle intervention",
    "lifestyle medicine group visit",
    "lifestyle medicine group visits",
    "group nutrition visit",
    "group nutrition visits",
    "group nutrition counseling",
    "group nutrition counselling",
    "group dietitian visit",
    "group dietitian visits",
    "diabetes group visit",
    "diabetes group visits",
    "prediabetes group visit",
    "prediabetes group visits",
    "obesity group visit",
    "obesity group visits",
    "weight management group visit",
    "weight management group visits",
    "cardiometabolic group visit",
    "cardiometabolic group visits",
]

GROUP_VISIT_NUTRITION_CARE_DOCUMENT_TERMS = [
    "group medical visit trial",
    "group medical visits trial",
    "shared medical appointment trial",
    "shared medical appointments trial",
    "group lifestyle intervention trial",
    "group-based lifestyle intervention trial",
    "group based lifestyle intervention trial",
    "group nutrition counseling intervention",
    "group nutrition counselling intervention",
    "group dietitian visit intervention",
    "diabetes group visit trial",
    "prediabetes group visit trial",
    "obesity group visit trial",
    "weight management group visit trial",
    "shared medical appointment systematic review",
    "group medical visit systematic review",
]

GROUP_VISIT_PRIORITIES = {
    "busca1": 2,
    "busca2a": 4,
    "busca2b": 5,
    "artigo3_framework": 3,
}


def _extend_unique(existing: list[str], additions: list[str]) -> list[str]:
    seen = {item.lower() for item in existing}
    for item in additions:
        value = item.strip()
        if not value or value.lower() in seen:
            continue
        existing.append(value)
        seen.add(value.lower())
    return existing


def apply_group_visit_extensions() -> None:
    block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS.setdefault(
        "group_visit_nutrition_care",
        {"terms": [], "document_terms": []},
    )
    block["terms"] = _extend_unique(
        block.setdefault("terms", []),
        GROUP_VISIT_NUTRITION_CARE_TERMS,
    )
    block["document_terms"] = _extend_unique(
        block.setdefault("document_terms", []),
        GROUP_VISIT_NUTRITION_CARE_DOCUMENT_TERMS,
    )

    for workstream, priority in GROUP_VISIT_PRIORITIES.items():
        existing = [
            (name, value)
            for name, value in semantic_blocks.WORKSTREAM_SEMANTIC_PRIORITIES.get(
                workstream,
                [],
            )
            if name != "group_visit_nutrition_care"
        ]
        semantic_blocks.WORKSTREAM_SEMANTIC_PRIORITIES[workstream] = [
            ("group_visit_nutrition_care", priority),
            *existing,
        ]
