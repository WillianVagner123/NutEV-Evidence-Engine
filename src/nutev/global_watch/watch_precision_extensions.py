from __future__ import annotations

from collections.abc import MutableSequence

from nutev.global_watch import watch_query_builder as query_builder
from nutev.global_watch.watch_config import WATCH_CATEGORIES

ADIPOSITY_CLINICAL_TERMS = [
    "abdominal obesity",
    "central obesity",
    "visceral adiposity",
    "visceral fat",
    "waist circumference",
    "waist-to-height ratio",
    "waist to height ratio",
    "waist-to-hip ratio",
    "waist to hip ratio",
]

DIABETES_REMISSION_TERMS = [
    "type 2 diabetes remission",
    "diabetes remission",
    "remission of type 2 diabetes",
]

_OBESITY_CATEGORY = "obesity_cardiometabolic"
_PATCHED = False


def _append_missing(target: MutableSequence[str], terms: list[str]) -> None:
    seen = {str(value).strip().lower() for value in target}
    for term in terms:
        normalized = term.strip().lower()
        if normalized and normalized not in seen:
            target.append(term)
            seen.add(normalized)


def _extend_seed_group(group: list[str], terms: list[str]) -> None:
    _append_missing(group, terms)


def apply_precision_extensions() -> None:
    global _PATCHED
    if _PATCHED:
        return

    context_terms = query_builder.CATEGORY_CONTEXT_TERMS.setdefault(_OBESITY_CATEGORY, [])
    _append_missing(context_terms, [*ADIPOSITY_CLINICAL_TERMS, *DIABETES_REMISSION_TERMS])

    canonical_terms = WATCH_CATEGORIES.setdefault(_OBESITY_CATEGORY, [])
    _append_missing(canonical_terms, [*ADIPOSITY_CLINICAL_TERMS, *DIABETES_REMISSION_TERMS])

    quick_groups = query_builder.QUICK_MODE_SEED_GROUPS.setdefault(_OBESITY_CATEGORY, [])
    if len(quick_groups) >= 1:
        _extend_seed_group(quick_groups[0], ADIPOSITY_CLINICAL_TERMS)
    if len(quick_groups) >= 2:
        _extend_seed_group(quick_groups[1], DIABETES_REMISSION_TERMS)

    _PATCHED = True


apply_precision_extensions()
