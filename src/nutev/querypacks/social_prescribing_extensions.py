from __future__ import annotations

from nutev.querypacks import semantic_blocks

SOCIAL_PRESCRIBING_NUTRITION_TERMS = [
    "social prescribing for nutrition",
    "social prescribing for healthy eating",
    "social prescribing for diet",
    "social prescribing for food insecurity",
    "social prescribing for nutrition security",
    "social prescribing for obesity",
    "social prescribing for weight management",
    "social prescribing for type 2 diabetes",
    "social prescribing for cardiometabolic risk",
    "nutrition social prescribing",
    "dietary social prescribing",
    "food social prescribing",
    "healthy eating social prescribing",
    "food access social prescribing",
    "social prescribing nutrition referral",
    "social prescribing dietitian referral",
    "social prescribing dietitian",
    "social prescribing registered dietitian",
    "social prescribing nutrition program",
    "social prescribing nutrition programme",
    "social prescribing food access program",
    "social prescribing food access programme",
    "link worker nutrition referral",
    "link worker food access referral",
    "community connector nutrition referral",
    "community connector food access referral",
]

SOCIAL_PRESCRIBING_NUTRITION_DOCUMENT_TERMS = [
    "social prescribing nutrition intervention",
    "social prescribing nutrition program evaluation",
    "social prescribing nutrition programme evaluation",
    "social prescribing dietitian referral program",
    "social prescribing dietitian referral programme",
    "social prescribing food access intervention",
    "social prescribing food access program evaluation",
    "social prescribing food access programme evaluation",
    "social prescribing food insecurity intervention",
    "social prescribing nutrition security intervention",
    "social prescribing weight management intervention",
    "social prescribing type 2 diabetes intervention",
    "social prescribing cardiometabolic intervention",
]


def _extend_unique(existing: list[str], additions: list[str]) -> list[str]:
    seen = {str(item).lower() for item in existing}
    for item in additions:
        value = str(item).strip()
        if not value or value.lower() in seen:
            continue
        existing.append(value)
        seen.add(value.lower())
    return existing


def _extend_semantic_block(block_name: str) -> None:
    block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS.setdefault(
        block_name,
        {"terms": [], "document_terms": []},
    )
    block["terms"] = _extend_unique(
        block.setdefault("terms", []),
        SOCIAL_PRESCRIBING_NUTRITION_TERMS,
    )
    block["document_terms"] = _extend_unique(
        block.setdefault("document_terms", []),
        SOCIAL_PRESCRIBING_NUTRITION_DOCUMENT_TERMS,
    )


def apply_social_prescribing_nutrition_extensions() -> None:
    for block_name in (
        "equity_access",
        "food_prescription_programs",
        "implementation_science",
        "lifestyle_nutrition_patterns",
    ):
        _extend_semantic_block(block_name)
