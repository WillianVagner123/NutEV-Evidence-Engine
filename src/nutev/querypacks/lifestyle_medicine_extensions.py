from __future__ import annotations

from nutev.querypacks import semantic_blocks

LIFESTYLE_MEDICINE_PRACTICE_TERMS = [
    "lifestyle medicine practice",
    "lifestyle medicine practices",
    "lifestyle medicine clinic",
    "lifestyle medicine clinics",
    "lifestyle medicine service",
    "lifestyle medicine services",
    "lifestyle medicine program",
    "lifestyle medicine programme",
    "lifestyle medicine programs",
    "lifestyle medicine programmes",
    "lifestyle medicine referral",
    "lifestyle medicine referrals",
    "lifestyle medicine prescription",
    "lifestyle medicine prescriptions",
    "therapeutic lifestyle prescription",
    "therapeutic lifestyle prescriptions",
    "lifestyle medicine counseling",
    "lifestyle medicine counselling",
    "lifestyle medicine competencies",
    "lifestyle medicine competency",
    "lifestyle medicine curriculum",
    "lifestyle medicine curricula",
]

LIFESTYLE_MEDICINE_PRACTICE_DOCUMENT_TERMS = [
    "lifestyle medicine guideline",
    "lifestyle medicine guidelines",
    "lifestyle medicine practice guideline",
    "lifestyle medicine practice guidelines",
    "lifestyle medicine consensus",
    "lifestyle medicine consensus statement",
    "lifestyle medicine position statement",
    "lifestyle medicine position paper",
    "lifestyle medicine competency framework",
    "lifestyle medicine curriculum",
    "lifestyle medicine curricula",
    "lifestyle medicine program evaluation",
    "lifestyle medicine programme evaluation",
    "lifestyle medicine service evaluation",
    "lifestyle medicine implementation",
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


def apply_lifestyle_medicine_extensions() -> None:
    for block_name in (
        "lifestyle_nutrition_patterns",
        "implementation_science",
        "nutrition_care_delivery",
    ):
        _extend_semantic_block(
            block_name,
            terms=LIFESTYLE_MEDICINE_PRACTICE_TERMS,
            document_terms=LIFESTYLE_MEDICINE_PRACTICE_DOCUMENT_TERMS,
        )
