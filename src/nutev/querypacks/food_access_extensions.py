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
]

FOOD_ACCESS_REFERRAL_PROGRAMME_TERMS = [
    "food prescription programme",
    "produce prescription programme",
    "healthy food prescription program",
    "healthy food prescription programme",
    "food as medicine program",
    "food as medicine programme",
    "food is medicine program",
    "food is medicine programme",
    "nutrition assistance programme",
    "nutrition assistance programmes",
    "nutrition security program",
    "nutrition security programme",
    "food pantry referral",
    "food pantry referral program",
    "food pantry referral programme",
    "food as medicine referral",
    "food is medicine referral",
    "produce prescription referral",
    "medically tailored food referral",
    "nutrition security referral",
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
]

FOOD_ACCESS_REFERRAL_PROGRAMME_DOCUMENT_TERMS = [
    "food prescription programme evaluation",
    "produce prescription programme evaluation",
    "healthy food prescription program evaluation",
    "healthy food prescription programme evaluation",
    "food as medicine programme evaluation",
    "food is medicine programme evaluation",
    "nutrition security programme evaluation",
    "food pantry referral programme evaluation",
    "produce prescription referral program",
    "medically tailored food referral program",
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
    terms = FOOD_ACCESS_BENEFIT_TERMS + FOOD_ACCESS_REFERRAL_PROGRAMME_TERMS
    document_terms = (
        FOOD_ACCESS_BENEFIT_DOCUMENT_TERMS
        + FOOD_ACCESS_REFERRAL_PROGRAMME_DOCUMENT_TERMS
    )
    for block_name in ("equity_access", "food_prescription_programs"):
        _extend_semantic_block(
            block_name,
            terms=terms,
            document_terms=document_terms,
        )
    _extend_semantic_block(
        "implementation_science",
        terms=terms,
        document_terms=document_terms,
    )
