from __future__ import annotations

from nutev.querypacks import semantic_blocks

SARCOPENIC_OBESITY_NUTRITION_TERMS = [
    "sarcopenic obesity",
    "sarcopenic adiposity",
    "obesity-related sarcopenia",
    "obesity related sarcopenia",
    "muscle mass and obesity",
    "low muscle mass obesity",
    "low muscle strength obesity",
    "dynapenic obesity",
    "protein intake and obesity",
    "dietary protein and obesity",
    "higher protein diet obesity",
    "high protein diet obesity",
    "protein-enriched diet obesity",
    "protein enriched diet obesity",
    "protein supplementation obesity",
    "oral nutrition supplement obesity",
    "oral nutritional supplement obesity",
    "resistance training and diet obesity",
    "resistance exercise and diet obesity",
    "combined diet and resistance training obesity",
    "combined diet and resistance exercise obesity",
]

SARCOPENIC_OBESITY_DOCUMENT_TERMS = [
    "sarcopenic obesity guideline",
    "sarcopenic obesity consensus",
    "sarcopenic obesity position statement",
    "sarcopenic obesity systematic review",
    "sarcopenic obesity meta-analysis",
    "sarcopenic obesity intervention trial",
    "protein intake obesity systematic review",
    "dietary protein obesity systematic review",
    "protein supplementation obesity trial",
    "oral nutrition supplement obesity trial",
    "combined diet and resistance training trial",
    "combined diet and resistance exercise trial",
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


def apply_sarcopenic_obesity_extensions() -> None:
    for block_name in (
        "cardiometabolic_precision",
        "lifestyle_nutrition_patterns",
        "nutrition_care_delivery",
        "adherence_persistence",
    ):
        _extend_semantic_block(
            block_name,
            terms=SARCOPENIC_OBESITY_NUTRITION_TERMS,
            document_terms=SARCOPENIC_OBESITY_DOCUMENT_TERMS,
        )
    _prioritize_semantic_block(
        "sarcopenic_obesity_nutrition",
        {"busca2a": 4, "busca2b": 5},
    )
    _extend_semantic_block(
        "sarcopenic_obesity_nutrition",
        terms=SARCOPENIC_OBESITY_NUTRITION_TERMS,
        document_terms=SARCOPENIC_OBESITY_DOCUMENT_TERMS,
    )
