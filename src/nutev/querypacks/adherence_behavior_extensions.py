from __future__ import annotations

from nutev.querypacks import semantic_blocks

ADHERENCE_MAINTENANCE_TERMS = [
    "long-term dietary adherence",
    "long term dietary adherence",
    "dietary adherence maintenance",
    "diet maintenance",
    "dietary maintenance",
    "behavioral maintenance",
    "behavioural maintenance",
    "weight maintenance",
    "weight regain prevention",
    "relapse prevention",
    "lapse management",
    "dietary relapse prevention",
    "habit formation",
    "healthy habit formation",
    "habit-based intervention",
    "habit based intervention",
    "dietary habit formation",
    "eating habit formation",
    "dietary self-monitoring",
    "dietary self monitoring",
    "food self-monitoring",
    "food self monitoring",
    "dietary self-regulation",
    "dietary self regulation",
    "eating self-regulation",
    "eating self regulation",
    "implementation intentions",
    "action planning",
    "coping planning",
    "problem solving",
    "goal setting",
    "engagement",
    "participant engagement",
    "intervention engagement",
    "retention",
    "participant retention",
    "persistence",
]

ADHERENCE_MAINTENANCE_DOCUMENT_TERMS = [
    "dietary adherence maintenance trial",
    "long-term dietary adherence trial",
    "long term dietary adherence trial",
    "dietary self-monitoring intervention",
    "dietary self regulation intervention",
    "eating self-regulation intervention",
    "habit formation intervention",
    "habit-based intervention trial",
    "relapse prevention intervention",
    "weight regain prevention trial",
    "weight maintenance intervention",
    "behavioral maintenance intervention",
    "participant engagement intervention",
    "retention strategy trial",
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


def apply_adherence_behavior_extensions() -> None:
    for block_name in ("adherence_persistence", "implementation_science"):
        _extend_semantic_block(
            block_name,
            terms=ADHERENCE_MAINTENANCE_TERMS,
            document_terms=ADHERENCE_MAINTENANCE_DOCUMENT_TERMS,
        )
    _prioritize_semantic_block(
        "adherence_persistence",
        {"busca2b": 6, "artigo3_framework": 5, "a3": 5},
    )
