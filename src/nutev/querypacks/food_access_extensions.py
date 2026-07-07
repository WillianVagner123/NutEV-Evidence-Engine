from __future__ import annotations

from nutev.querypacks import semantic_blocks

FOOD_ACCESS_BENEFIT_TERMS = [
    "grocery prescription",
    "grocery prescriptions",
    "grocery prescription program",
    "grocery prescription programme",
    "healthy grocery prescription",
    "grocery prescription intervention",
    "grocery prescription diabetes",
    "grocery prescription cardiometabolic",
    "food benefit",
    "food benefits",
    "healthy food benefit",
    "healthy food benefits",
    "food benefit program",
    "food benefit programme",
    "healthy food benefit program",
    "healthy food benefit programme",
    "healthy food benefit intervention",
    "healthy food benefit diabetes",
    "food as medicine benefit",
    "food is medicine benefit",
    "produce prescription benefit",
    "fresh food box",
    "fresh food boxes",
    "healthy food box",
    "healthy food boxes",
    "produce box",
    "produce boxes",
    "fruit and vegetable box",
    "fruit and vegetable boxes",
    "fruit and vegetable incentive program",
    "fruit and vegetable incentive programme",
    "medically tailored meal program",
    "medically tailored meal programme",
    "medically tailored meals program",
    "medically tailored meals programme",
    "medically tailored meal intervention",
    "medically tailored meals intervention",
    "medically tailored meals diabetes",
    "medically tailored meals hypertension",
    "medically tailored meals cardiometabolic",
    "medically tailored grocery box",
    "medically tailored grocery boxes",
    "medically tailored grocery program",
    "medically tailored grocery programme",
    "medically tailored groceries program",
    "medically tailored groceries programme",
    "medically tailored grocery intervention",
    "medically tailored groceries intervention",
    "medically tailored food program",
    "medically tailored food programme",
    "medically tailored food intervention",
    "medically tailored nutrition program",
    "medically tailored nutrition programme",
    "medically tailored nutrition intervention",
    "food as medicine cardiometabolic",
    "food as medicine diabetes",
    "food as medicine hypertension",
    "food is medicine cardiometabolic",
    "food is medicine diabetes",
    "produce prescription diabetes",
    "produce prescription cardiometabolic",
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
    "food pharmacy",
    "food pharmacies",
    "food pharmacy program",
    "food farmacy",
    "food farmacies",
    "food farmacy program",
    "community-supported food program",
    "community supported food program",
]

FOOD_ACCESS_BENEFIT_DOCUMENT_TERMS = [
    "grocery prescription program evaluation",
    "grocery prescription intervention trial",
    "grocery prescription systematic review",
    "healthy grocery prescription intervention",
    "healthy food benefit program evaluation",
    "healthy food benefit intervention trial",
    "food benefit program evaluation",
    "food as medicine benefit evaluation",
    "food is medicine benefit evaluation",
    "food as medicine systematic review",
    "food is medicine systematic review",
    "food as medicine consensus",
    "food is medicine consensus",
    "fresh food box program evaluation",
    "produce box program evaluation",
    "fruit and vegetable incentive program evaluation",
    "medically tailored meal program evaluation",
    "medically tailored meal intervention trial",
    "medically tailored meal systematic review",
    "medically tailored meals program evaluation",
    "medically tailored meals intervention trial",
    "medically tailored meals systematic review",
    "medically tailored grocery program evaluation",
    "medically tailored grocery intervention trial",
    "medically tailored groceries program evaluation",
    "medically tailored groceries intervention trial",
    "medically tailored food program evaluation",
    "medically tailored food intervention trial",
    "medically tailored nutrition program evaluation",
    "medically tailored nutrition intervention trial",
    "produce prescription systematic review",
    "produce prescription program evaluation",
    "produce prescription intervention trial",
    "nutrition security screening evaluation",
    "nutrition insecurity screening evaluation",
    "food insecurity screening evaluation",
    "hunger vital sign evaluation",
    "screen and intervene evaluation",
    "food access referral program evaluation",
    "food pharmacy program evaluation",
    "food farmacy program evaluation",
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
