from __future__ import annotations

from nutev.querypacks import semantic_blocks

BEHAVIOURAL_VARIANT_TERMS = [
    "behavioural intervention",
    "behavioural lifestyle intervention",
    "behavioural weight management",
    "behavioural weight loss",
    "behavioural dietary intervention",
    "behavioural nutrition intervention",
    "behavioural counselling",
    "behavioural counseling",
    "behaviour change",
    "behaviour change intervention",
    "behaviour change maintenance",
    "behavioural maintenance",
    "dietary behaviour change",
    "eating behaviour change",
    "behavioural support",
    "behavioural support intervention",
]

BEHAVIOURAL_VARIANT_DOCUMENT_TERMS = [
    "behaviour change trial",
    "behaviour change intervention",
    "behavioural lifestyle intervention trial",
    "behavioural weight management trial",
    "behavioural weight loss trial",
    "behavioural dietary intervention",
    "behavioural nutrition intervention",
    "behavioural support intervention",
    "dietary behaviour change intervention",
    "eating behaviour change intervention",
]

BEHAVIOURAL_VARIANT_BLOCKS = (
    "implementation_science",
    "adherence_persistence",
    "lifestyle_nutrition_patterns",
)


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


def apply_behavioural_variant_extensions() -> None:
    for block_name in BEHAVIOURAL_VARIANT_BLOCKS:
        _extend_semantic_block(
            block_name,
            terms=BEHAVIOURAL_VARIANT_TERMS,
            document_terms=BEHAVIOURAL_VARIANT_DOCUMENT_TERMS,
        )
