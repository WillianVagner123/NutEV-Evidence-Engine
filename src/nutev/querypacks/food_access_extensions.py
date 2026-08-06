from __future__ import annotations

from nutev.querypacks import semantic_blocks

FOOD_ACCESS_BENEFIT_TERMS = [
    "grocery prescription",
    "grocery prescriptions",
    "grocery prescription program",
    "grocery prescription programme",
    "healthy grocery prescription",
    "food benefit",
    "food benefits",
    "healthy food benefit",
    "healthy food benefits",
    "food benefit program",
    "food benefit programme",
    "healthy food benefit program",
    "healthy food benefit programme",
    "fresh food box",
    "fresh food boxes",
    "healthy food box",
    "healthy food boxes",
    "produce box",
    "produce boxes",
    "fruit and vegetable box",
    "fruit and vegetable boxes",
    "medically tailored grocery box",
    "medically tailored grocery boxes",
    "medically tailored grocery program",
    "medically tailored grocery programme",
    "medically tailored groceries program",
    "medically tailored groceries programme",
    "medically tailored nutrition",
    "medically tailored nutrition program",
    "medically tailored nutrition programme",
    "nutrition assistance program",
    "nutrition assistance programme",
    "nutrition assistance intervention",
    "nutrition resource referral",
    "nutrition resource navigation",
    "nutrition security screening",
    "nutrition insecurity screening",
    "nutrition security intervention",
    "nutrition insecurity intervention",
    "food insecurity screening",
    "screening for food insecurity",
    "hunger vital sign",
    "screen and intervene",
    "food access screening",
    "food access referral",
    "healthy food referral",
    "food resource referral",
    "food resource navigation",
    "food pharmacy",
    "food pharmacies",
    "food pharmacy program",
    "fresh food pharmacy",
    "fresh food pharmacies",
    "food farmacy",
    "food farmacies",
    "food farmacy program",
    "fresh produce prescription",
    "fresh produce prescriptions",
    "fresh produce prescription program",
    "fresh produce prescription programme",
    "fruit and vegetable incentive",
    "fruit and vegetable incentives",
    "community-supported food program",
    "community supported food program",
]

FOOD_ACCESS_BENEFIT_DOCUMENT_TERMS = [
    "grocery prescription program evaluation",
    "grocery prescription intervention trial",
    "healthy grocery prescription intervention",
    "healthy food benefit program evaluation",
    "food benefit program evaluation",
    "fresh food box program evaluation",
    "produce box program evaluation",
    "medically tailored grocery program evaluation",
    "medically tailored grocery intervention trial",
    "medically tailored groceries program evaluation",
    "medically tailored nutrition program evaluation",
    "medically tailored nutrition intervention trial",
    "nutrition assistance program evaluation",
    "nutrition assistance intervention trial",
    "nutrition resource referral program evaluation",
    "nutrition resource navigation program evaluation",
    "nutrition security screening evaluation",
    "nutrition insecurity screening evaluation",
    "food insecurity screening evaluation",
    "hunger vital sign evaluation",
    "screen and intervene evaluation",
    "food access referral program evaluation",
    "food resource referral program evaluation",
    "food resource navigation program evaluation",
    "food pharmacy program evaluation",
    "fresh food pharmacy program evaluation",
    "food farmacy program evaluation",
    "fresh produce prescription program evaluation",
    "fresh produce prescription intervention trial",
    "fruit and vegetable incentive program evaluation",
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


def apply_food_access_benefit_extensions() -> None:
    for block_name in ("equity_access", "food_prescription_programs"):
        _extend_semantic_block(
            block_name,
            terms=FOOD_ACCESS_BENEFIT_TERMS,
            document_terms=FOOD_ACCESS_BENEFIT_DOCUMENT_TERMS,
        )
    _extend_semantic_block(
        "implementation_science",
        terms=FOOD_ACCESS_BENEFIT_TERMS,
        document_terms=FOOD_ACCESS_BENEFIT_DOCUMENT_TERMS,
    )
