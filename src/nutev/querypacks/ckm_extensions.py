from __future__ import annotations

from nutev.querypacks import semantic_blocks

CKM_NUTRITION_TERMS = [
    "cardiovascular-kidney-metabolic nutrition",
    "cardiovascular kidney metabolic nutrition",
    "cardiovascular-kidney-metabolic care",
    "cardiovascular kidney metabolic care",
    "cardiovascular-kidney-metabolic disease",
    "cardiovascular kidney metabolic disease",
    "cardiovascular-kidney-metabolic prevention",
    "cardiovascular kidney metabolic prevention",
    "cardiovascular-kidney-metabolic risk management",
    "cardiovascular kidney metabolic risk management",
    "ckm nutrition",
    "ckm care",
    "ckm prevention",
    "ckm risk management",
    "ckm syndrome nutrition",
    "ckm syndrome diet",
    "ckm health nutrition",
    "ckm health diet",
    "ckm risk nutrition",
    "ckm risk diet",
]

CKM_NUTRITION_DOCUMENT_TERMS = [
    "ckm scientific statement",
    "ckm presidential advisory",
    "ckm clinical practice guideline",
    "ckm consensus statement",
    "ckm clinical decision pathway",
    "ckm practice guidance",
    "ckm systematic review",
    "cardiovascular-kidney-metabolic scientific statement",
    "cardiovascular kidney metabolic scientific statement",
    "cardiovascular-kidney-metabolic consensus statement",
    "cardiovascular kidney metabolic consensus statement",
    "cardiovascular-kidney-metabolic clinical practice guideline",
    "cardiovascular kidney metabolic clinical practice guideline",
    "cardiovascular-kidney-metabolic clinical decision pathway",
    "cardiovascular kidney metabolic clinical decision pathway",
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


def apply_ckm_extensions() -> None:
    block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS.setdefault(
        "cardiometabolic_precision",
        {"terms": [], "document_terms": []},
    )
    block["terms"] = _extend_unique(block.setdefault("terms", []), CKM_NUTRITION_TERMS)
    block["document_terms"] = _extend_unique(
        block.setdefault("document_terms", []),
        CKM_NUTRITION_DOCUMENT_TERMS,
    )
