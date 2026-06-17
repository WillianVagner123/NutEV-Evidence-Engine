from __future__ import annotations

from collections.abc import Iterable

CKM_CARDIOMETABOLIC_TERMS = [
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

CKM_SCORING_BONUS_TERMS: tuple[tuple[str, float], ...] = (
    ("cardiovascular-kidney-metabolic syndrome", 14),
    ("cardiovascular kidney metabolic syndrome", 14),
    ("cardiovascular-kidney-metabolic health", 12),
    ("cardiovascular kidney metabolic health", 12),
    ("cardiovascular-kidney-metabolic risk", 12),
    ("cardiovascular kidney metabolic risk", 12),
    ("cardiovascular-kidney-metabolic nutrition", 14),
    ("cardiovascular kidney metabolic nutrition", 14),
    ("cardio-kidney-metabolic syndrome", 12),
    ("cardio kidney metabolic syndrome", 12),
    ("cardio-kidney-metabolic nutrition", 12),
    ("cardio kidney metabolic nutrition", 12),
    ("cardiorenal metabolic syndrome", 10),
    ("ckm syndrome", 12),
    ("ckm health", 10),
    ("ckm risk", 10),
    ("ckm nutrition", 12),
)


def _extend_list_once(values: list[str], terms: Iterable[str]) -> None:
    seen = {value.lower() for value in values}
    for term in terms:
        key = term.lower()
        if key in seen:
            continue
        values.append(term)
        seen.add(key)


def _extend_tuple_once(
    values: tuple[tuple[str, float], ...],
    terms: Iterable[tuple[str, float]],
) -> tuple[tuple[str, float], ...]:
    seen = {term.lower() for term, _ in values}
    additions = tuple((term, weight) for term, weight in terms if term.lower() not in seen)
    return values + additions


def _extend_scope_tuple_once(values: tuple[str, ...], terms: Iterable[str]) -> tuple[str, ...]:
    seen = {value.lower() for value in values}
    additions = tuple(term.lower() for term in terms if term.lower() not in seen)
    return values + additions


def apply_global_watch_semantic_expansions() -> None:
    from nutev.global_watch import watch_query_builder, watch_scoring

    obesity_context = watch_query_builder.CATEGORY_CONTEXT_TERMS.setdefault(
        "obesity_cardiometabolic",
        [],
    )
    _extend_list_once(obesity_context, CKM_CARDIOMETABOLIC_TERMS)

    quick_groups = watch_query_builder.QUICK_MODE_SEED_GROUPS.get(
        "obesity_cardiometabolic",
        [],
    )
    if len(quick_groups) >= 2:
        _extend_list_once(quick_groups[1], CKM_CARDIOMETABOLIC_TERMS)

    watch_scoring.BONUS_TERMS = _extend_tuple_once(
        watch_scoring.BONUS_TERMS,
        CKM_SCORING_BONUS_TERMS,
    )
    watch_scoring.NUTMEV_SCOPE_TERMS = _extend_scope_tuple_once(
        watch_scoring.NUTMEV_SCOPE_TERMS,
        CKM_CARDIOMETABOLIC_TERMS,
    )
