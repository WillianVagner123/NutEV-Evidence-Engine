from __future__ import annotations

from nutev.querypacks import semantic_blocks

BODY_COMPOSITION_NUTRITION_TERMS = [
    "sarcopenic obesity",
    "sarcopenic overweight",
    "body composition change",
    "body composition changes",
    "lean mass preservation",
    "fat-free mass preservation",
    "fat free mass preservation",
    "muscle preservation during weight loss",
    "lean mass during weight loss",
    "fat-free mass during weight loss",
    "fat free mass during weight loss",
    "dietary protein during weight loss",
    "protein intake during weight loss",
    "protein adequacy during weight loss",
    "protein distribution during weight loss",
    "high-protein diet for weight loss",
    "high protein diet for weight loss",
    "protein quality during weight loss",
]

BODY_COMPOSITION_NUTRITION_DOCUMENT_TERMS = [
    "sarcopenic obesity guideline",
    "sarcopenic obesity consensus",
    "sarcopenic obesity systematic review",
    "body composition weight loss trial",
    "body composition weight loss systematic review",
    "lean mass preservation trial",
    "lean mass preservation systematic review",
    "fat-free mass preservation trial",
    "fat free mass preservation trial",
    "dietary protein weight loss trial",
    "dietary protein weight loss systematic review",
    "high-protein diet weight loss trial",
    "high protein diet weight loss trial",
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


def apply_body_composition_extensions() -> None:
    _extend_semantic_block(
        "body_composition_nutrition",
        terms=BODY_COMPOSITION_NUTRITION_TERMS,
        document_terms=BODY_COMPOSITION_NUTRITION_DOCUMENT_TERMS,
    )
    _prioritize_semantic_block(
        "body_composition_nutrition",
        {"busca2b": 5, "busca2a": 4, "artigo3_framework": 3},
    )
