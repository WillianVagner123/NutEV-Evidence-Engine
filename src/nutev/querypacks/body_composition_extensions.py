from __future__ import annotations

from nutev.querypacks import semantic_blocks

BODY_COMPOSITION_NUTRITION_TERMS = [
    "sarcopenic obesity",
    "sarcopenic adiposity",
    "low muscle mass obesity",
    "low muscle strength obesity",
    "lean mass preservation",
    "fat-free mass preservation",
    "fat free mass preservation",
    "muscle mass preservation",
    "muscle preservation during weight loss",
    "lean mass during weight loss",
    "fat-free mass during weight loss",
    "fat free mass during weight loss",
    "body composition during weight loss",
    "body composition weight maintenance",
    "protein intake during weight loss",
    "dietary protein during weight loss",
    "protein adequacy during weight loss",
    "higher protein diet weight loss",
    "high-protein diet weight loss",
    "high protein diet weight loss",
    "protein distribution",
    "protein pacing",
    "protein quality",
    "protein adequacy",
    "muscle mass maintenance",
    "lean mass maintenance",
    "fat-free mass maintenance",
    "fat free mass maintenance",
]

BODY_COMPOSITION_NUTRITION_DOCUMENT_TERMS = [
    "sarcopenic obesity guideline",
    "sarcopenic obesity consensus",
    "sarcopenic obesity systematic review",
    "sarcopenic obesity meta-analysis",
    "body composition weight loss systematic review",
    "body composition weight loss meta-analysis",
    "lean mass preservation trial",
    "muscle mass preservation trial",
    "protein intake weight loss trial",
    "dietary protein weight loss trial",
    "protein adequacy weight loss trial",
    "higher protein diet weight loss systematic review",
    "high-protein diet weight loss systematic review",
    "high protein diet weight loss systematic review",
    "protein intake weight maintenance trial",
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
    block_name: str, priorities: dict[str, int]) -> None:
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
        {"busca2a": 4, "busca2b": 5},
    )
    for block_name in (
        "cardiometabolic_precision",
        "lifestyle_nutrition_patterns",
        "adherence_persistence",
    ):
        _extend_semantic_block(
            block_name,
            terms=BODY_COMPOSITION_NUTRITION_TERMS,
            document_terms=BODY_COMPOSITION_NUTRITION_DOCUMENT_TERMS,
        )
