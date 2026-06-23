from __future__ import annotations

from nutev.querypacks import semantic_blocks

CARDIOVASCULAR_HEALTH_METRICS_TERMS = [
    "life's essential 8",
    "lifes essential 8",
    "life essential 8",
    "essential 8",
    "life's simple 7",
    "lifes simple 7",
    "life simple 7",
    "simple 7",
    "ideal cardiovascular health",
    "cardiovascular health score",
    "cardiovascular health metrics",
    "cardiovascular health construct",
    "cardiovascular health behaviors",
    "cardiovascular health behaviour",
    "cardiovascular health behavior",
    "diet score and cardiovascular health",
    "healthy diet score and cardiovascular health",
    "diet quality and cardiovascular health",
    "cardiometabolic health score",
    "cardiometabolic health metrics",
]

CARDIOVASCULAR_HEALTH_METRICS_DOCUMENT_TERMS = [
    "life's essential 8 scientific statement",
    "lifes essential 8 scientific statement",
    "life's simple 7 scientific statement",
    "lifes simple 7 scientific statement",
    "ideal cardiovascular health scientific statement",
    "cardiovascular health score systematic review",
    "cardiovascular health metrics systematic review",
    "cardiovascular health metrics guideline",
    "cardiovascular health metrics consensus",
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


def apply_cardiovascular_health_metrics_extensions() -> None:
    _extend_semantic_block(
        "cardiovascular_health_metrics",
        terms=CARDIOVASCULAR_HEALTH_METRICS_TERMS,
        document_terms=CARDIOVASCULAR_HEALTH_METRICS_DOCUMENT_TERMS,
    )
    _prioritize_semantic_block(
        "cardiovascular_health_metrics",
        {"busca1": 3, "busca2a": 5, "busca2b": 5},
    )
