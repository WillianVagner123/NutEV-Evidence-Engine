from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from nutev.global_watch import watch_config

SUSTAINABLE_HEALTHY_DIET_TERMS = [
    "sustainable healthy diets",
    "sustainable healthy diet",
    "healthy sustainable diets",
    "healthy sustainable diet",
    "healthy and sustainable diets",
    "healthy and sustainable diet",
    "sustainable dietary patterns",
    "sustainable dietary pattern",
    "sustainable diets",
    "sustainable diet",
]

SUSTAINABLE_HEALTHY_DIET_BONUS_TERMS = [
    ("sustainable healthy diets", 12),
    ("sustainable healthy diet", 10),
    ("healthy sustainable diets", 12),
    ("healthy sustainable diet", 10),
    ("healthy and sustainable diets", 12),
    ("healthy and sustainable diet", 10),
    ("sustainable dietary patterns", 12),
    ("sustainable dietary pattern", 10),
    ("sustainable diets", 10),
    ("sustainable diet", 8),
]


def _dedupe_preserve_order(values: Sequence[Any]) -> list[Any]:
    seen: set[str] = set()
    unique_values: list[Any] = []
    for value in values:
        key = str(value).strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        unique_values.append(value)
    return unique_values


def _extend_category_terms(category: str, terms: Sequence[str]) -> None:
    category_terms = watch_config.WATCH_CATEGORIES.get(category)
    if not isinstance(category_terms, list):
        return
    if any(isinstance(term, list) for term in category_terms):
        return
    category_terms[:] = _dedupe_preserve_order([*category_terms, *terms])


def _extend_quick_seed_group(category: str, group_index: int, terms: Sequence[str]) -> None:
    from nutev.global_watch import watch_query_builder

    groups = watch_query_builder.QUICK_MODE_SEED_GROUPS.get(category)
    if not isinstance(groups, list) or group_index >= len(groups):
        return
    group = groups[group_index]
    if not isinstance(group, list):
        return
    group[:] = _dedupe_preserve_order([*group, *terms])


def _extend_query_context(category: str, terms: Sequence[str]) -> None:
    from nutev.global_watch import watch_query_builder

    context_terms = watch_query_builder.CATEGORY_CONTEXT_TERMS.get(category)
    if not isinstance(context_terms, list):
        return
    context_terms[:] = _dedupe_preserve_order([*context_terms, *terms])


def _extend_scoring_terms() -> None:
    from nutev.global_watch import watch_scoring

    watch_scoring.BONUS_TERMS = tuple(
        _dedupe_preserve_order(
            [
                *watch_scoring.BONUS_TERMS,
                *SUSTAINABLE_HEALTHY_DIET_BONUS_TERMS,
            ]
        )
    )
    watch_scoring.NUTMEV_SCOPE_TERMS = tuple(
        _dedupe_preserve_order(
            [
                *watch_scoring.NUTMEV_SCOPE_TERMS,
                *SUSTAINABLE_HEALTHY_DIET_TERMS,
            ]
        )
    )


def apply_sustainable_diet_extensions() -> None:
    _extend_category_terms("diet_patterns", SUSTAINABLE_HEALTHY_DIET_TERMS)
    _extend_quick_seed_group("diet_patterns", 2, SUSTAINABLE_HEALTHY_DIET_TERMS)
    _extend_query_context("diet_patterns", SUSTAINABLE_HEALTHY_DIET_TERMS)
    _extend_scoring_terms()


apply_sustainable_diet_extensions()
