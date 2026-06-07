from __future__ import annotations

from collections.abc import Iterable

CKM_TERMS = [
    "cardiovascular-kidney-metabolic syndrome",
    "cardiovascular kidney metabolic syndrome",
    "cardiovascular-kidney-metabolic health",
    "cardiovascular kidney metabolic health",
    "cardiovascular-kidney-metabolic risk",
    "cardiovascular kidney metabolic risk",
    "CKM syndrome",
    "CKM health",
    "CKM risk",
]

CKM_WEIGHTED_TERMS: tuple[tuple[str, float], ...] = tuple(
    (term.lower(), 14.0) for term in CKM_TERMS
)


def _extend_unique(existing: list[str], additions: Iterable[str]) -> list[str]:
    seen = {str(item).lower() for item in existing}
    for item in additions:
        value = str(item).strip()
        if not value or value.lower() in seen:
            continue
        existing.append(value)
        seen.add(value.lower())
    return existing


def _extend_weighted_tuple(
    existing: tuple[tuple[str, float], ...],
    additions: Iterable[tuple[str, float]],
) -> tuple[tuple[str, float], ...]:
    seen = {term.lower() for term, _ in existing}
    output = list(existing)
    for term, weight in additions:
        value = str(term).strip().lower()
        if not value or value in seen:
            continue
        output.append((value, weight))
        seen.add(value)
    return tuple(output)


def _extend_tuple(existing: tuple[str, ...], additions: Iterable[str]) -> tuple[str, ...]:
    seen = {term.lower() for term in existing}
    output = list(existing)
    for term in additions:
        value = str(term).strip().lower()
        if not value or value in seen:
            continue
        output.append(value)
        seen.add(value)
    return tuple(output)


def apply_ckm_extensions() -> None:
    from nutev.global_watch import watch_query_builder, watch_scoring

    context_terms = watch_query_builder.CATEGORY_CONTEXT_TERMS.setdefault(
        "obesity_cardiometabolic",
        [],
    )
    _extend_unique(context_terms, CKM_TERMS)

    quick_groups = watch_query_builder.QUICK_MODE_SEED_GROUPS.setdefault(
        "obesity_cardiometabolic",
        [],
    )
    if len(quick_groups) >= 2:
        _extend_unique(quick_groups[1], CKM_TERMS)
    else:
        quick_groups.append(list(CKM_TERMS))

    for mode_groups_name in (
        "THESIS_MODE_SEED_GROUPS",
        "EXHAUSTIVE_MODE_SEED_GROUPS",
    ):
        mode_groups = getattr(watch_query_builder, mode_groups_name, {})
        category_groups = mode_groups.get("obesity_cardiometabolic")
        if category_groups:
            _extend_unique(category_groups[0], CKM_TERMS)

    watch_scoring.BONUS_TERMS = _extend_weighted_tuple(  # type: ignore[misc]
        watch_scoring.BONUS_TERMS,
        CKM_WEIGHTED_TERMS,
    )
    watch_scoring.NUTMEV_SCOPE_TERMS = _extend_tuple(  # type: ignore[misc]
        watch_scoring.NUTMEV_SCOPE_TERMS,
        CKM_TERMS,
    )
