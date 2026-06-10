from __future__ import annotations

from nutev.querypacks import semantic_blocks

FOOD_ENVIRONMENT_POLICY_TERMS = [
    "food environment intervention",
    "food environment interventions",
    "retail food environment intervention",
    "retail food environment interventions",
    "healthy food retail intervention",
    "healthy food retail interventions",
    "healthy food procurement",
    "healthy food procurement policy",
    "institutional food procurement",
    "public food procurement",
    "food service guidelines",
    "healthy food service guidelines",
    "nutrition standards for food service",
    "healthy default",
    "healthy defaults",
    "choice architecture",
    "healthy choice architecture",
    "choice architecture intervention",
    "nudge intervention",
    "nudging intervention",
    "menu labeling policy",
    "menu labelling policy",
]

FOOD_ENVIRONMENT_POLICY_DOCUMENT_TERMS = [
    "food environment policy",
    "food environment policy evaluation",
    "food environment intervention study",
    "retail food environment intervention",
    "healthy food retail intervention",
    "healthy food procurement policy",
    "institutional food procurement policy",
    "public food procurement policy",
    "food service guideline",
    "food service guidelines",
    "healthy food service guideline",
    "healthy food service guidelines",
    "nutrition standards for food service",
    "choice architecture intervention",
    "nudge intervention trial",
    "menu labeling policy evaluation",
    "menu labelling policy evaluation",
]

TARGET_BLOCKS = (
    "food_literacy_agency",
    "equity_access",
    "implementation_science",
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


def apply_food_environment_policy_extensions() -> None:
    for block_name in TARGET_BLOCKS:
        block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS.setdefault(
            block_name,
            {"terms": [], "document_terms": []},
        )
        block["terms"] = _extend_unique(
            block.setdefault("terms", []),
            FOOD_ENVIRONMENT_POLICY_TERMS,
        )
        block["document_terms"] = _extend_unique(
            block.setdefault("document_terms", []),
            FOOD_ENVIRONMENT_POLICY_DOCUMENT_TERMS,
        )


apply_food_environment_policy_extensions()
