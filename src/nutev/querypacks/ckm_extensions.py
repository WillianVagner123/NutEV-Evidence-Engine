from __future__ import annotations

from nutev.querypacks import semantic_blocks

CKM_RENAL_METABOLIC_TERMS = [
    "cardiovascular-kidney-metabolic syndrome",
    "cardiovascular kidney metabolic syndrome",
    "cardiovascular-kidney-metabolic health",
    "cardiovascular kidney metabolic health",
    "cardiovascular-kidney-metabolic risk",
    "cardiovascular kidney metabolic risk",
    "ckm syndrome",
    "ckm health",
    "ckm risk",
    "chronic kidney disease",
    "ckd",
    "diabetic kidney disease",
    "diabetic nephropathy",
    "albuminuria",
    "kidney function",
    "estimated glomerular filtration rate",
    "egfr",
]

CKM_RENAL_METABOLIC_DOCUMENT_TERMS = [
    "scientific statement",
    "presidential advisory",
    "clinical practice guideline",
    "consensus statement",
    "clinical decision pathway",
    "practice guidance",
    "systematic review",
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
    block["terms"] = _extend_unique(
        block.setdefault("terms", []),
        CKM_RENAL_METABOLIC_TERMS,
    )
    block["document_terms"] = _extend_unique(
        block.setdefault("document_terms", []),
        CKM_RENAL_METABOLIC_DOCUMENT_TERMS,
    )
