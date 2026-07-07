from __future__ import annotations

from nutev.querypacks import semantic_blocks

FOOD_ENVIRONMENT_POLICY_TERMS = [
    "food environment intervention",
    "food environment interventions",
    "retail food environment intervention",
    "retail food environment interventions",
    "healthy food retail intervention",
    "healthy food retail interventions",
    "healthy choice architecture",
    "choice architecture intervention",
    "choice architecture interventions",
    "food procurement policy",
    "healthy food procurement policy",
    "institutional food procurement",
    "public food procurement",
    "food service guideline",
    "food service guidelines",
    "healthy food service guideline",
    "healthy food service guidelines",
    "nutrition standards for food service",
    "nutrition standards for food services",
    "menu labeling policy",
    "menu labelling policy",
    "front-of-pack labeling policy",
    "front-of-pack labelling policy",
]

FOOD_ENVIRONMENT_POLICY_DOCUMENT_TERMS = [
    "food environment intervention study",
    "food environment policy evaluation",
    "retail food environment intervention",
    "healthy food retail intervention",
    "choice architecture intervention",
    "food procurement policy evaluation",
    "healthy food procurement policy evaluation",
    "food service guideline",
    "food service guidelines",
    "healthy food service guideline",
    "healthy food service guidelines",
    "nutrition standards for food service",
    "menu labeling policy evaluation",
    "front-of-pack labeling policy evaluation",
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


def apply_food_environment_extensions() -> None:
    for block_name in (
        "food_literacy_agency",
        "equity_access",
        "implementation_science",
    ):
        _extend_semantic_block(
            block_name,
            terms=FOOD_ENVIRONMENT_POLICY_TERMS,
            document_terms=FOOD_ENVIRONMENT_POLICY_DOCUMENT_TERMS,
        )


apply_food_environment_extensions()
