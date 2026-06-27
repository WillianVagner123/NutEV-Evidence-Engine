from __future__ import annotations

from nutev.querypacks import semantic_blocks

BLOOD_PRESSURE_NUTRITION_TERMS = [
    "blood pressure reduction",
    "blood pressure control",
    "blood pressure management",
    "hypertension nutrition therapy",
    "hypertension dietary intervention",
    "hypertension lifestyle intervention",
    "dietary sodium reduction",
    "sodium reduction",
    "salt reduction",
    "salt restriction",
    "low sodium diet",
    "low-sodium diet",
    "sodium restriction",
    "potassium intake",
    "dietary potassium",
    "sodium potassium ratio",
    "sodium-to-potassium ratio",
    "dash diet adherence",
    "dash dietary pattern adherence",
]

BLOOD_PRESSURE_NUTRITION_DOCUMENT_TERMS = [
    "hypertension nutrition guideline",
    "hypertension dietary guideline",
    "hypertension lifestyle guideline",
    "hypertension nutrition consensus",
    "hypertension dietary consensus",
    "blood pressure dietary intervention trial",
    "sodium reduction trial",
    "salt reduction trial",
    "dash diet systematic review",
    "dash diet meta-analysis",
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


def apply_blood_pressure_nutrition_extensions() -> None:
    for block_name in (
        "cardiometabolic_precision",
        "lifestyle_nutrition_patterns",
    ):
        _extend_semantic_block(
            block_name,
            terms=BLOOD_PRESSURE_NUTRITION_TERMS,
            document_terms=BLOOD_PRESSURE_NUTRITION_DOCUMENT_TERMS,
        )
