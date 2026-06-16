from __future__ import annotations

from nutev.querypacks import semantic_blocks

NUTRITION_CARE_DELIVERY_TERMS = [
    "nutrition care delivery",
    "nutrition care model",
    "nutrition care models",
    "nutrition care implementation",
    "nutrition care coordination",
    "nutrition referral",
    "nutrition care referral",
    "medical nutrition therapy delivery",
    "medical nutrition therapy implementation",
    "diet therapy implementation",
    "dietitian-led care",
    "dietitian led care",
    "dietitian-led program",
    "dietitian led program",
    "dietitian-led programme",
    "dietitian led programme",
    "dietitian-led lifestyle program",
    "dietitian led lifestyle program",
    "dietitian-led weight management",
    "dietitian led weight management",
    "registered dietitian referral",
    "registered dietitian nutritionist referral",
    "dietitian referral",
    "interprofessional nutrition care",
    "team-based nutrition care",
    "team based nutrition care",
    "primary care nutrition referral",
    "primary care nutrition intervention",
    "primary care dietitian",
]

NUTRITION_CARE_DELIVERY_DOCUMENT_TERMS = [
    "nutrition care delivery model",
    "nutrition care implementation study",
    "nutrition care pathway implementation",
    "nutrition care protocol implementation",
    "nutrition care coordination model",
    "medical nutrition therapy implementation study",
    "medical nutrition therapy delivery model",
    "dietitian-led care model",
    "dietitian led care model",
    "dietitian-led program evaluation",
    "dietitian led program evaluation",
    "dietitian-led programme evaluation",
    "dietitian led programme evaluation",
    "registered dietitian referral pathway",
    "dietitian referral pathway",
    "primary care nutrition referral pathway",
    "interprofessional nutrition care model",
    "team-based nutrition care model",
    "team based nutrition care model",
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


def apply_nutrition_care_extensions() -> None:
    for block_name in ("nutrition_care_delivery", "implementation_science"):
        _extend_semantic_block(
            block_name,
            terms=NUTRITION_CARE_DELIVERY_TERMS,
            document_terms=NUTRITION_CARE_DELIVERY_DOCUMENT_TERMS,
        )
    _extend_semantic_block(
        "adherence_persistence",
        terms=[
            "dietitian-led lifestyle program",
            "dietitian led lifestyle program",
            "dietitian-led weight management",
            "dietitian led weight management",
            "nutrition care coordination",
            "medical nutrition therapy implementation",
        ],
        document_terms=[
            "dietitian-led program evaluation",
            "dietitian led program evaluation",
            "medical nutrition therapy implementation study",
            "nutrition care implementation study",
        ],
    )


apply_nutrition_care_extensions()
