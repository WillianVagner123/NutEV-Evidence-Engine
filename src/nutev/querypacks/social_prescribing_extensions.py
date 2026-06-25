from __future__ import annotations

from nutev.querypacks import semantic_blocks

SOCIAL_PRESCRIBING_FOOD_REFERRAL_TERMS = [
    "social prescribing nutrition",
    "social prescribing diet",
    "social prescribing for food insecurity",
    "social prescribing food insecurity",
    "food referral pathway",
    "nutrition referral pathway",
    "clinical-community food referral",
    "clinical community food referral",
    "community food referral",
    "community food referrals",
    "food resource referral",
    "food resource referrals",
    "food resource navigation",
    "food resource navigator",
    "community resource referral",
    "community resource referrals",
    "produce prescription referral",
    "food pharmacy referral",
    "fresh food pharmacy",
    "fresh food pharmacy referral",
    "medically tailored meal referral",
    "medically tailored meals referral",
    "medically tailored grocery referral",
    "medically tailored groceries referral",
    "closed-loop food referral",
    "closed loop food referral",
]

SOCIAL_PRESCRIBING_FOOD_REFERRAL_DOCUMENT_TERMS = [
    "social prescribing nutrition program",
    "social prescribing nutrition programme",
    "social prescribing food insecurity program",
    "food referral pathway evaluation",
    "nutrition referral pathway evaluation",
    "clinical-community food referral program",
    "clinical community food referral program",
    "community food referral program",
    "food resource referral program",
    "food resource navigation program",
    "food resource navigation intervention",
    "produce prescription referral program",
    "food pharmacy referral program",
    "fresh food pharmacy program",
    "fresh food pharmacy intervention",
    "medically tailored meal referral program",
    "medically tailored grocery referral program",
    "closed-loop food referral program",
    "closed loop food referral program",
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


def _prioritize_semantic_block(block_name: str, priorities: dict[str, int]) -> None:
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


def apply_social_prescribing_food_referral_extensions() -> None:
    for block_name in ("equity_access", "food_prescription_programs"):
        _extend_semantic_block(
            block_name,
            terms=SOCIAL_PRESCRIBING_FOOD_REFERRAL_TERMS,
            document_terms=SOCIAL_PRESCRIBING_FOOD_REFERRAL_DOCUMENT_TERMS,
        )
    _extend_semantic_block(
        "implementation_science",
        terms=SOCIAL_PRESCRIBING_FOOD_REFERRAL_TERMS,
        document_terms=SOCIAL_PRESCRIBING_FOOD_REFERRAL_DOCUMENT_TERMS,
    )
    _prioritize_semantic_block(
        "equity_access",
        {"busca1": 5, "busca2b": 4, "artigo3_framework": 3},
    )
