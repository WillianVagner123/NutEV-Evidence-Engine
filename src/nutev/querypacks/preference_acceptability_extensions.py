from __future__ import annotations

from nutev.querypacks import semantic_blocks

PREFERENCE_ACCEPTABILITY_TERMS = [
    "patient preference",
    "patient preferences",
    "food preference",
    "food preferences",
    "diet preference",
    "diet preferences",
    "dietary preference",
    "dietary preferences",
    "meal preference",
    "meal preferences",
    "taste preference",
    "taste preferences",
    "palatability",
    "food palatability",
    "diet acceptability",
    "dietary acceptability",
    "meal acceptability",
    "intervention acceptability",
    "nutrition intervention acceptability",
    "dietary intervention acceptability",
    "treatment acceptability",
    "diet satisfaction",
    "dietary satisfaction",
    "meal satisfaction",
    "patient-centered nutrition",
    "patient centred nutrition",
    "patient-centered diet",
    "patient centred diet",
    "person-centered nutrition",
    "person centred nutrition",
    "person-centered dietary intervention",
    "person centred dietary intervention",
    "preference-sensitive",
    "preference sensitive",
    "preference-sensitive nutrition",
    "preference sensitive nutrition",
    "shared decision making for nutrition",
    "shared decision making for diet",
    "nutrition shared decision making",
    "dietary shared decision making",
    "cultural food preference",
    "cultural food preferences",
    "culturally tailored diet",
    "culturally tailored nutrition",
    "culturally tailored dietary intervention",
    "culturally adapted nutrition",
    "culturally adapted dietary intervention",
]

PREFERENCE_ACCEPTABILITY_DOCUMENT_TERMS = [
    "patient preference study",
    "patient preferences study",
    "food preference study",
    "food preferences study",
    "dietary preference study",
    "dietary preferences study",
    "diet acceptability study",
    "dietary acceptability study",
    "intervention acceptability study",
    "nutrition intervention acceptability study",
    "dietary intervention acceptability study",
    "treatment acceptability study",
    "diet satisfaction study",
    "dietary satisfaction study",
    "patient-centered nutrition intervention",
    "patient centred nutrition intervention",
    "person-centered dietary intervention",
    "person centred dietary intervention",
    "preference-sensitive nutrition intervention",
    "preference sensitive nutrition intervention",
    "shared decision making nutrition intervention",
    "shared decision making dietary intervention",
    "culturally tailored dietary intervention",
    "culturally adapted nutrition intervention",
    "culturally adapted dietary intervention",
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


def _prioritize_semantic_block(block_name: str, priorities: dict[str, int]) -> None:
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


def apply_preference_acceptability_extensions() -> None:
    _extend_semantic_block(
        "preference_acceptability",
        terms=PREFERENCE_ACCEPTABILITY_TERMS,
        document_terms=PREFERENCE_ACCEPTABILITY_DOCUMENT_TERMS,
    )
    _prioritize_semantic_block(
        "preference_acceptability",
        {"busca2b": 5, "artigo3_framework": 4, "busca1": 3, "busca2a": 3},
    )
