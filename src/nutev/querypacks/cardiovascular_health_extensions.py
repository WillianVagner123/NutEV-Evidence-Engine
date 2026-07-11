from __future__ import annotations

from nutev.querypacks import semantic_blocks

CARDIOVASCULAR_HEALTH_NUTRITION_TERMS = [
    "life's essential 8",
    "lifes essential 8",
    "life essential 8",
    "cardiovascular health score",
    "cardiovascular health metrics",
    "ideal cardiovascular health",
    "cardiovascular health diet",
    "cardiovascular health nutrition",
    "cardiovascular health dietary pattern",
    "cardiovascular health promotion",
    "heart healthy diet",
    "heart-healthy diet",
    "heart healthy dietary pattern",
    "heart-healthy dietary pattern",
    "dietary guidance for cardiovascular health",
    "nutrition guidance for cardiovascular health",
]

CARDIOVASCULAR_HEALTH_NUTRITION_DOCUMENT_TERMS = [
    "life's essential 8 scientific statement",
    "lifes essential 8 scientific statement",
    "life essential 8 scientific statement",
    "cardiovascular health scientific statement",
    "cardiovascular health guideline",
    "cardiovascular health consensus statement",
    "heart healthy diet guideline",
    "heart-healthy diet guideline",
    "dietary guidance for cardiovascular health",
    "nutrition guidance for cardiovascular health",
    "cardiovascular health systematic review",
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


def apply_cardiovascular_health_extensions() -> None:
    _extend_semantic_block(
        "cardiovascular_health_nutrition",
        terms=CARDIOVASCULAR_HEALTH_NUTRITION_TERMS,
        document_terms=CARDIOVASCULAR_HEALTH_NUTRITION_DOCUMENT_TERMS,
    )
    _prioritize_semantic_block(
        "cardiovascular_health_nutrition",
        {"busca1": 3, "busca2a": 5, "busca2b": 5},
    )

    for block_name in (
        "cardiometabolic_precision",
        "lifestyle_nutrition_patterns",
        "evidence_synthesis",
    ):
        _extend_semantic_block(
            block_name,
            terms=CARDIOVASCULAR_HEALTH_NUTRITION_TERMS,
            document_terms=CARDIOVASCULAR_HEALTH_NUTRITION_DOCUMENT_TERMS,
        )
