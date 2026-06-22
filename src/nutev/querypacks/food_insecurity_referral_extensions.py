from __future__ import annotations

from nutev.querypacks import semantic_blocks

FOOD_INSECURITY_REFERRAL_TERMS = [
    "food insecurity screening and referral",
    "food insecurity screening referral",
    "screening and referral for food insecurity",
    "nutrition insecurity screening and referral",
    "nutrition insecurity screening referral",
    "food insecurity referral",
    "nutrition insecurity referral",
    "food resource referral",
    "food resource navigation",
    "food resource navigator",
    "food resource navigators",
    "food resource connection",
    "food resource connections",
    "food access navigation",
    "food access navigator",
    "food access navigators",
    "nutrition resource referral",
    "nutrition resource navigation",
    "community food resource referral",
    "community food resource navigation",
    "clinical-community food referral",
    "clinical community food referral",
    "clinic-to-community food referral",
    "clinic to community food referral",
]

FOOD_INSECURITY_REFERRAL_DOCUMENT_TERMS = [
    "food insecurity screening and referral program",
    "food insecurity screening referral program",
    "screening and referral for food insecurity program",
    "nutrition insecurity screening and referral program",
    "food insecurity referral program",
    "food resource referral program",
    "food resource navigation program",
    "food access navigation program",
    "nutrition resource referral program",
    "nutrition resource navigation program",
    "community food resource referral program",
    "community food resource navigation program",
    "clinical-community food referral program",
    "clinic-to-community food referral program",
    "food insecurity screening implementation study",
    "food insecurity referral implementation study",
    "food resource navigation implementation study",
    "food access navigation implementation study",
    "food insecurity screening quality improvement",
    "food insecurity referral quality improvement",
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


def apply_food_insecurity_referral_extensions() -> None:
    for block_name in ("equity_access", "food_prescription_programs"):
        _extend_semantic_block(
            block_name,
            terms=FOOD_INSECURITY_REFERRAL_TERMS,
            document_terms=FOOD_INSECURITY_REFERRAL_DOCUMENT_TERMS,
        )
    _extend_semantic_block(
        "implementation_science",
        terms=FOOD_INSECURITY_REFERRAL_TERMS,
        document_terms=FOOD_INSECURITY_REFERRAL_DOCUMENT_TERMS,
    )
