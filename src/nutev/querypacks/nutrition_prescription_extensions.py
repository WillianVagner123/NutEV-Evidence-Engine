from __future__ import annotations

from nutev.querypacks import semantic_blocks

NUTRITION_PRESCRIPTION_TERMS = [
    "nutrition prescription",
    "nutrition prescriptions",
    "diet prescription",
    "diet prescriptions",
    "dietary prescription",
    "dietary prescriptions",
    "healthy eating prescription",
    "healthy eating prescriptions",
    "therapeutic diet prescription",
    "therapeutic dietary prescription",
    "medical nutrition prescription",
    "prescribed nutrition plan",
    "prescribed diet plan",
    "prescribed dietary plan",
    "lifestyle prescription",
    "lifestyle prescriptions",
    "lifestyle medicine prescription",
    "lifestyle medicine prescriptions",
    "lifestyle prescription for obesity",
    "lifestyle prescription for cardiometabolic risk",
    "nutrition prescription for obesity",
    "nutrition prescription for cardiometabolic risk",
    "nutrition prescription for type 2 diabetes",
    "dietary prescription for type 2 diabetes",
]

NUTRITION_PRESCRIPTION_DOCUMENT_TERMS = [
    "nutrition prescription guideline",
    "nutrition prescription intervention",
    "nutrition prescription trial",
    "nutrition prescription program",
    "nutrition prescription programme",
    "diet prescription intervention",
    "dietary prescription intervention",
    "healthy eating prescription program",
    "healthy eating prescription programme",
    "healthy eating prescription program evaluation",
    "lifestyle prescription intervention",
    "lifestyle medicine prescription intervention",
    "lifestyle prescription program",
    "lifestyle prescription programme",
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


def apply_nutrition_prescription_extensions() -> None:
    for block_name in (
        "nutrition_care_delivery",
        "lifestyle_nutrition_patterns",
        "implementation_science",
        "adherence_persistence",
    ):
        _extend_semantic_block(
            block_name,
            terms=NUTRITION_PRESCRIPTION_TERMS,
            document_terms=NUTRITION_PRESCRIPTION_DOCUMENT_TERMS,
        )
