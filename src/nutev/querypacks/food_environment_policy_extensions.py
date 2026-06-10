from __future__ import annotations

from nutev.querypacks import semantic_blocks

BLOCK_NAME = "food_environment_policy"

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

PRIORITY_TARGETS = {
    "busca1": 5,
    "busca2b": 5,
    "artigo3_framework": 4,
}


def _extend_unique(existing: list[str], additions: list[str]) -> list[str]:
    seen = {item.lower() for item in existing}
    for item in additions:
        value = item.strip()
        if not value or value.lower() in seen:
            continue
        existing.append(value)
        seen.add(value.lower())
    return existing


def _prepend_priority(workstream: str, priority: int) -> None:
    priorities = semantic_blocks.WORKSTREAM_SEMANTIC_PRIORITIES.setdefault(
        workstream,
        [],
    )
    filtered = [(name, value) for name, value in priorities if name != BLOCK_NAME]
    priorities[:] = [(BLOCK_NAME, priority), *filtered]


def apply_food_environment_policy_extensions() -> None:
    block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS.setdefault(
        BLOCK_NAME,
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
    for workstream, priority in PRIORITY_TARGETS.items():
        _prepend_priority(workstream, priority)


apply_food_environment_policy_extensions()
