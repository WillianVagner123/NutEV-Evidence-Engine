from __future__ import annotations

from nutev.global_watch import watch_scoring

CKM_BONUS_TERMS: tuple[tuple[str, float], ...] = (
    ("cardiovascular-kidney-metabolic syndrome", 14),
    ("cardiovascular kidney metabolic syndrome", 14),
    ("cardiovascular-kidney-metabolic health", 12),
    ("cardiovascular kidney metabolic health", 12),
    ("cardiovascular-kidney-metabolic risk", 12),
    ("cardiovascular kidney metabolic risk", 12),
    ("cardiovascular-kidney-metabolic nutrition", 14),
    ("cardiovascular kidney metabolic nutrition", 14),
    ("cardio-kidney-metabolic syndrome", 14),
    ("cardio kidney metabolic syndrome", 14),
    ("cardio-kidney-metabolic nutrition", 14),
    ("cardio kidney metabolic nutrition", 14),
    ("cardiorenal metabolic syndrome", 12),
    ("ckm syndrome", 12),
    ("ckm health", 10),
    ("ckm risk", 10),
    ("ckm nutrition", 12),
)

CKM_SCOPE_TERMS: tuple[str, ...] = tuple(term for term, _ in CKM_BONUS_TERMS)


def apply_watch_scoring_extensions() -> None:
    if getattr(watch_scoring, "_nutev_ckm_scoring_patched", False):
        return
    watch_scoring.BONUS_TERMS = (*watch_scoring.BONUS_TERMS, *CKM_BONUS_TERMS)
    watch_scoring.NUTMEV_SCOPE_TERMS = (
        *watch_scoring.NUTMEV_SCOPE_TERMS,
        *CKM_SCOPE_TERMS,
    )
    watch_scoring._nutev_ckm_scoring_patched = True
