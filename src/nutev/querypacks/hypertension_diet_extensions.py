from __future__ import annotations

from nutev.querypacks import semantic_blocks

HYPERTENSION_DIET_TERMS = [
    "dietary sodium reduction",
    "sodium reduction",
    "salt reduction",
    "low sodium diet",
    "low-sodium diet",
    "reduced sodium diet",
    "reduced-sodium diet",
    "dietary salt reduction",
    "sodium intake reduction",
    "salt intake reduction",
    "dietary potassium",
    "potassium intake",
    "sodium potassium ratio",
    "sodium-to-potassium ratio",
    "salt substitute",
    "salt substitutes",
    "potassium-enriched salt",
    "potassium enriched salt",
    "DASH-Sodium",
    "dash sodium",
    "blood pressure dietary intervention",
    "hypertension dietary intervention",
    "dietary intervention for hypertension",
]

HYPERTENSION_DIET_DOCUMENT_TERMS = [
    "sodium reduction guideline",
    "salt reduction guideline",
    "dietary sodium guideline",
    "low sodium diet guideline",
    "dietary sodium systematic review",
    "salt reduction systematic review",
    "salt substitute trial",
    "salt substitute systematic review",
    "potassium-enriched salt trial",
    "potassium enriched salt trial",
    "DASH-Sodium trial",
    "blood pressure dietary intervention trial",
    "hypertension dietary intervention trial",
    "dietary intervention for hypertension trial",
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


def apply_hypertension_diet_extensions() -> None:
    _extend_semantic_block(
        "cardiometabolic_precision",
        terms=HYPERTENSION_DIET_TERMS,
        document_terms=HYPERTENSION_DIET_DOCUMENT_TERMS,
    )


apply_hypertension_diet_extensions()
