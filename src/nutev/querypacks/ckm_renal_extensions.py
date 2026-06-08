from __future__ import annotations

from nutev.querypacks import semantic_blocks

CKM_RENAL_NUTRITION_TERMS = [
    "cardio-kidney-metabolic syndrome",
    "cardio kidney metabolic syndrome",
    "cardio-kidney-metabolic health",
    "cardio kidney metabolic health",
    "cardio-kidney-metabolic risk",
    "cardio kidney metabolic risk",
    "cardiorenal metabolic syndrome",
    "cardiorenal metabolic risk",
    "cardiovascular renal metabolic syndrome",
    "cardiovascular renal metabolic risk",
    "chronic kidney disease cardiometabolic risk",
    "chronic kidney disease nutrition care",
    "ckd cardiometabolic risk",
    "ckd nutrition care",
    "diabetic kidney disease nutrition",
    "diabetic kidney disease nutrition care",
    "kidney health nutrition cardiometabolic",
    "renal nutrition cardiometabolic risk",
]

CKM_RENAL_DOCUMENT_TERMS = [
    "cardio-kidney-metabolic scientific statement",
    "cardio-kidney-metabolic consensus statement",
    "cardio-kidney-metabolic clinical practice guideline",
    "ckm scientific statement",
    "ckm consensus statement",
    "ckm clinical practice guideline",
    "chronic kidney disease nutrition guideline",
    "chronic kidney disease nutrition consensus",
    "diabetic kidney disease nutrition guideline",
    "diabetic kidney disease nutrition consensus",
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


def apply_ckm_renal_extensions() -> None:
    for block_name in ("cardiometabolic_precision", "nutrition_care_delivery"):
        _extend_semantic_block(
            block_name,
            terms=CKM_RENAL_NUTRITION_TERMS,
            document_terms=CKM_RENAL_DOCUMENT_TERMS,
        )
