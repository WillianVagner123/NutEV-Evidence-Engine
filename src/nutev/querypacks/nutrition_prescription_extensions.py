from __future__ import annotations

from nutev.querypacks import semantic_blocks

NUTRITION_PRESCRIPTION_TERMS = [
    "nutrition prescription",
    "nutrition prescriptions",
    "diet prescription",
    "diet prescriptions",
    "dietary prescription",
    "dietary prescriptions",
    "prescribed diet",
    "prescribed diets",
    "prescribed dietary intervention",
    "prescribed dietary interventions",
    "individualized nutrition prescription",
    "individualised nutrition prescription",
    "personalized nutrition prescription",
    "personalised nutrition prescription",
    "tailored nutrition prescription",
    "tailored dietary prescription",
]

NUTRITION_PRESCRIPTION_DOCUMENT_TERMS = [
    "nutrition prescription guideline",
    "nutrition prescription guidelines",
    "nutrition prescription protocol",
    "nutrition prescription protocols",
    "dietary prescription guideline",
    "dietary prescription guidelines",
    "dietary prescription protocol",
    "dietary prescription protocols",
    "diet prescription trial",
    "dietary prescription trial",
    "prescribed diet intervention",
    "prescribed dietary intervention",
    "personalized nutrition prescription framework",
    "personalised nutrition prescription framework",
]

TARGET_BLOCKS = (
    "nutrition_care_delivery",
    "lifestyle_nutrition_patterns",
    "adherence_persistence",
)


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


def apply_nutrition_prescription_extensions() -> None:
    for block_name in TARGET_BLOCKS:
        _extend_semantic_block(
            block_name,
            terms=NUTRITION_PRESCRIPTION_TERMS,
            document_terms=NUTRITION_PRESCRIPTION_DOCUMENT_TERMS,
        )
