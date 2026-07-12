from __future__ import annotations

from nutev.querypacks import semantic_blocks

ADHERENCE_ENGAGEMENT_TERMS = [
    "dietary intervention engagement",
    "nutrition intervention engagement",
    "intervention engagement",
    "participant engagement",
    "patient engagement",
    "dietary intervention retention",
    "nutrition intervention retention",
    "intervention retention",
    "program retention",
    "programme retention",
    "intervention dose",
    "dietary intervention dose",
    "nutrition intervention dose",
    "session attendance",
    "program attendance",
    "programme attendance",
    "counseling attendance",
    "counselling attendance",
    "treatment attendance",
    "adherence monitoring",
    "adherence support",
    "dropout prevention",
    "attrition prevention",
]

ADHERENCE_ENGAGEMENT_DOCUMENT_TERMS = [
    "dietary adherence intervention",
    "nutrition adherence intervention",
    "intervention engagement study",
    "dietary intervention engagement study",
    "nutrition intervention engagement study",
    "intervention retention study",
    "dietary intervention retention study",
    "nutrition intervention retention study",
    "intervention dose trial",
    "dietary intervention dose trial",
    "nutrition intervention dose trial",
    "session attendance trial",
    "program attendance study",
    "programme attendance study",
    "adherence monitoring intervention",
    "adherence support intervention",
    "dropout prevention intervention",
    "attrition prevention intervention",
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


def apply_adherence_engagement_extensions() -> None:
    _extend_semantic_block(
        "adherence_engagement_dose",
        terms=ADHERENCE_ENGAGEMENT_TERMS,
        document_terms=ADHERENCE_ENGAGEMENT_DOCUMENT_TERMS,
    )
    _prioritize_semantic_block(
        "adherence_engagement_dose",
        {"busca2b": 5, "artigo3_framework": 4, "busca2a": 3, "busca1": 3},
    )
