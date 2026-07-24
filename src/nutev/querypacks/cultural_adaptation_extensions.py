from __future__ import annotations

from nutev.querypacks import semantic_blocks

CULTURAL_ADAPTATION_TERMS = [
    "culturally tailored nutrition",
    "culturally tailored diet",
    "culturally tailored dietary intervention",
    "culturally adapted nutrition",
    "culturally adapted diet",
    "culturally adapted dietary intervention",
    "culturally appropriate nutrition",
    "culturally appropriate dietary advice",
    "culturally responsive nutrition counseling",
    "culturally responsive nutrition counselling",
    "culturally sensitive nutrition counseling",
    "culturally sensitive nutrition counselling",
    "culturally relevant dietary advice",
    "culturally congruent diet",
    "culturally congruent nutrition",
    "cultural adaptation nutrition",
    "cultural adaptation dietary intervention",
    "cultural tailoring nutrition",
    "cultural tailoring dietary intervention",
    "dietary acculturation",
    "food acculturation",
    "nutrition acculturation",
    "acculturation and diet",
    "acculturation and dietary pattern",
    "traditional dietary pattern",
    "traditional food pattern",
    "ethnic dietary pattern",
    "ethnic food pattern",
    "culturally tailored lifestyle intervention",
    "culturally adapted lifestyle intervention",
]

CULTURAL_ADAPTATION_DOCUMENT_TERMS = [
    "culturally tailored nutrition intervention",
    "culturally tailored dietary intervention",
    "culturally adapted nutrition intervention",
    "culturally adapted dietary intervention",
    "culturally appropriate nutrition education",
    "culturally responsive nutrition counseling",
    "culturally responsive nutrition counselling",
    "cultural adaptation framework",
    "cultural adaptation intervention",
    "cultural tailoring intervention",
    "dietary acculturation systematic review",
    "dietary acculturation intervention",
    "traditional dietary pattern systematic review",
    "ethnic dietary pattern systematic review",
    "culturally tailored lifestyle intervention",
    "culturally adapted lifestyle intervention",
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


def apply_cultural_adaptation_extensions() -> None:
    for block_name in (
        "equity_access",
        "adherence_persistence",
        "implementation_science",
        "lifestyle_nutrition_patterns",
    ):
        _extend_semantic_block(
            block_name,
            terms=CULTURAL_ADAPTATION_TERMS,
            document_terms=CULTURAL_ADAPTATION_DOCUMENT_TERMS,
        )
    _prioritize_semantic_block(
        "equity_access",
        {"busca1": 5, "busca2b": 5, "artigo3_framework": 4, "busca2a": 4},
    )
