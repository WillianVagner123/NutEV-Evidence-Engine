from __future__ import annotations

from nutev.querypacks import semantic_blocks

BODY_COMPOSITION_PRESERVATION_TERMS = [
    "sarcopenic obesity",
    "sarcopenic obese",
    "obesity sarcopenia",
    "sarcopenic adiposity",
    "dynapenic obesity",
    "muscle mass preservation",
    "lean mass preservation",
    "fat-free mass preservation",
    "fat free mass preservation",
    "appendicular lean mass",
    "appendicular skeletal muscle mass",
    "skeletal muscle mass",
    "muscle strength",
    "grip strength",
    "physical function",
    "body composition preservation",
    "body recomposition",
    "protein intake for weight loss",
    "dietary protein for weight loss",
    "higher protein diet",
    "high-protein diet",
    "high protein diet",
    "protein quality",
    "dietary protein quality",
    "plant protein quality",
    "protein distribution",
    "protein timing",
    "protein adequacy",
    "leucine",
    "essential amino acids",
    "resistance training nutrition",
]

BODY_COMPOSITION_PRESERVATION_DOCUMENT_TERMS = [
    "sarcopenic obesity guideline",
    "sarcopenic obesity consensus",
    "sarcopenic obesity systematic review",
    "sarcopenic obesity meta-analysis",
    "sarcopenic obesity intervention trial",
    "lean mass preservation trial",
    "muscle mass preservation trial",
    "weight loss lean mass trial",
    "weight loss body composition trial",
    "dietary protein intervention trial",
    "higher protein diet trial",
    "high-protein diet trial",
    "protein intake systematic review",
    "dietary protein systematic review",
    "protein quality systematic review",
    "body composition systematic review",
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


def apply_body_composition_extensions() -> None:
    _extend_semantic_block(
        "body_composition_preservation",
        terms=BODY_COMPOSITION_PRESERVATION_TERMS,
        document_terms=BODY_COMPOSITION_PRESERVATION_DOCUMENT_TERMS,
    )
    _prioritize_semantic_block(
        "body_composition_preservation",
        {"busca2a": 3, "busca2b": 4},
    )
