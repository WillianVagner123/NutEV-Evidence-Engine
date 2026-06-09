from __future__ import annotations

from nutev.querypacks import semantic_blocks


FOOD_BENEFIT_NAVIGATION_TERMS = [
    "health-related social needs",
    "health related social needs",
    "food benefit",
    "food benefits",
    "food benefit navigation",
    "food benefit referral",
    "food resource navigation",
    "food resource navigator",
    "healthy food benefit",
    "healthy food benefits",
    "nutrition benefit",
    "nutrition benefits",
    "snap produce incentive",
    "snap fruit and vegetable incentive",
    "fruit and vegetable incentive",
    "fruit and vegetable incentives",
    "fruit and vegetable incentive program",
    "fruit and vegetable incentive programme",
    "fresh food pharmacy",
    "fresh food pharmacy program",
    "fresh food pharmacy programme",
    "clinical-community food referral",
    "clinical community food referral",
]

FOOD_BENEFIT_NAVIGATION_DOCUMENT_TERMS = [
    "health-related social needs screening program",
    "health related social needs screening program",
    "food benefit navigation program",
    "food benefit referral program",
    "food resource navigation program",
    "healthy food benefit program",
    "nutrition benefit program",
    "snap produce incentive program",
    "fruit and vegetable incentive program",
    "fresh food pharmacy program",
    "clinical-community food referral program",
    "food resource navigation program evaluation",
    "healthy food benefit program evaluation",
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


def apply_food_access_extensions() -> None:
    for block_name in ("equity_access", "food_prescription_programs"):
        _extend_semantic_block(
            block_name,
            terms=FOOD_BENEFIT_NAVIGATION_TERMS,
            document_terms=FOOD_BENEFIT_NAVIGATION_DOCUMENT_TERMS,
        )


apply_food_access_extensions()
