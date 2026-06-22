from __future__ import annotations

from nutev.querypacks import semantic_blocks

DIETARY_HABIT_AUTOMATICITY_TERMS = [
    "dietary habit maintenance",
    "healthy eating habit maintenance",
    "nutrition habit maintenance",
    "eating habit maintenance",
    "dietary habit formation",
    "healthy eating habit formation",
    "nutrition habit formation",
    "eating habit formation",
    "dietary habit strength",
    "healthy eating habit strength",
    "eating habit strength",
    "dietary habit automaticity",
    "healthy eating automaticity",
    "eating habit automaticity",
    "habit-based dietary intervention",
    "habit based dietary intervention",
    "habit-based nutrition intervention",
    "habit based nutrition intervention",
    "habit-based weight management",
    "habit based weight management",
    "habit formation intervention",
    "habit maintenance intervention",
    "dietary routine formation",
    "healthy eating routine",
    "healthy eating routines",
    "meal routine planning",
    "meal routines intervention",
    "implementation intentions for diet",
    "dietary implementation intentions",
    "healthy eating implementation intentions",
    "if-then planning for diet",
    "if then planning for diet",
    "cue-based eating behavior",
    "cue based eating behavior",
    "cue-based eating behaviour",
    "cue based eating behaviour",
]

DIETARY_HABIT_AUTOMATICITY_DOCUMENT_TERMS = [
    "habit-based dietary intervention",
    "habit based dietary intervention",
    "habit-based nutrition intervention",
    "habit based nutrition intervention",
    "habit-based weight management trial",
    "habit based weight management trial",
    "habit formation intervention",
    "habit maintenance intervention",
    "dietary habit formation intervention",
    "healthy eating habit formation intervention",
    "dietary habit maintenance intervention",
    "healthy eating habit maintenance intervention",
    "dietary habit automaticity scale",
    "self-report habit index diet",
    "self report habit index diet",
    "self-report behavioural automaticity index diet",
    "self report behavioural automaticity index diet",
    "self-report behavioral automaticity index diet",
    "self report behavioral automaticity index diet",
    "dietary implementation intentions trial",
    "healthy eating implementation intentions trial",
    "if-then planning dietary intervention",
    "if then planning dietary intervention",
    "meal routine intervention",
]

HABIT_AUTOMATICITY_PRIORITIES = {
    "busca2b": 6,
    "a3": 5,
    "artigo3_framework": 5,
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


def _prioritize_semantic_block(block_name: str) -> None:
    for workstream, priority in HABIT_AUTOMATICITY_PRIORITIES.items():
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


def apply_habit_automaticity_extensions() -> None:
    for block_name in (
        "adherence_persistence",
        "implementation_science",
        "lifestyle_nutrition_patterns",
    ):
        _extend_semantic_block(
            block_name,
            terms=DIETARY_HABIT_AUTOMATICITY_TERMS,
            document_terms=DIETARY_HABIT_AUTOMATICITY_DOCUMENT_TERMS,
        )
    _prioritize_semantic_block("adherence_persistence")


apply_habit_automaticity_extensions()
