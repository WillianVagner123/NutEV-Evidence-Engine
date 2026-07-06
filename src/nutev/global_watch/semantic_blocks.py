from __future__ import annotations

from collections.abc import Iterable


def dedupe_terms(terms: Iterable[str]) -> list[str]:
    """Return terms in first-seen order with case-insensitive deduplication."""
    seen: set[str] = set()
    unique_terms: list[str] = []
    for term in terms:
        value = str(term).strip()
        if not value:
            continue
        lowered = value.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique_terms.append(value)
    return unique_terms


CKM_NUTRITION_ANCHOR_TERMS = [
    "nutrition",
    "diet",
    "dietary",
    "food",
    "dietary pattern",
    "medical nutrition therapy",
    "nutrition care",
]

CKM_SYNDROME_TERMS = [
    "cardiovascular-kidney-metabolic syndrome",
    "cardiovascular kidney metabolic syndrome",
    "cardiovascular-kidney-metabolic health",
    "cardiovascular kidney metabolic health",
    "cardiovascular-kidney-metabolic risk",
    "cardiovascular kidney metabolic risk",
    "cardiovascular-kidney-metabolic nutrition",
    "cardiovascular kidney metabolic nutrition",
    "cardio-kidney-metabolic syndrome",
    "cardio kidney metabolic syndrome",
    "cardio-kidney-metabolic nutrition",
    "cardio kidney metabolic nutrition",
    "cardiorenal metabolic syndrome",
    "CKM syndrome",
    "CKM health",
    "CKM risk",
    "CKM nutrition",
]

CKM_CONDITION_TERMS = [
    "obesity",
    "adiposity",
    "cardiometabolic risk",
    "metabolic syndrome",
    "type 2 diabetes",
    "prediabetes",
    "hypertension",
    "dyslipidemia",
    "dyslipidaemia",
    "chronic kidney disease",
    "kidney disease",
    "renal disease",
    "albuminuria",
    "MASLD",
    "NAFLD",
    "steatotic liver disease",
]

CKM_DOCUMENT_TYPE_TERMS = [
    "clinical practice guideline",
    "guideline",
    "consensus statement",
    "scientific statement",
    "position statement",
    "practice guidance",
    "clinical decision pathway",
    "standards of care",
    "systematic review",
    "meta-analysis",
    "umbrella review",
]


def ckm_watch_terms() -> list[str]:
    """Terms for CKM monitoring anchored to NutMEV nutrition scope."""
    return dedupe_terms(
        [
            *CKM_SYNDROME_TERMS,
            *CKM_CONDITION_TERMS,
            *CKM_NUTRITION_ANCHOR_TERMS,
            *CKM_DOCUMENT_TYPE_TERMS,
        ]
    )
