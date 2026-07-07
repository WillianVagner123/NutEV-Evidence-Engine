from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from nutev.global_watch import watch_config

GROUP_VISIT_NUTRITION_TERMS = [
    "shared medical appointment nutrition",
    "shared medical appointments nutrition",
    "shared medical appointment diabetes",
    "shared medical appointments diabetes",
    "shared medical appointment obesity",
    "shared medical appointments obesity",
    "shared medical appointment weight management",
    "group medical visit nutrition",
    "group medical visits nutrition",
    "group medical visit diabetes",
    "group medical visits diabetes",
    "group medical visit obesity",
    "group medical visits obesity",
    "group medical visit weight management",
    "lifestyle medicine group visit",
    "lifestyle medicine group visits",
    "lifestyle medicine shared medical appointment",
    "group-based nutrition intervention",
    "group based nutrition intervention",
    "group-based dietary intervention",
    "group based dietary intervention",
    "group lifestyle intervention diabetes",
    "group lifestyle intervention obesity",
]

GROUP_VISIT_BONUS_TERMS = [
    ("shared medical appointment nutrition", 20),
    ("shared medical appointments nutrition", 20),
    ("shared medical appointment diabetes", 18),
    ("shared medical appointments diabetes", 18),
    ("shared medical appointment obesity", 18),
    ("shared medical appointments obesity", 18),
    ("shared medical appointment weight management", 20),
    ("group medical visit nutrition", 20),
    ("group medical visits nutrition", 20),
    ("group medical visit diabetes", 18),
    ("group medical visits diabetes", 18),
    ("group medical visit obesity", 18),
    ("group medical visits obesity", 18),
    ("group medical visit weight management", 20),
    ("lifestyle medicine group visit", 20),
    ("lifestyle medicine group visits", 20),
    ("lifestyle medicine shared medical appointment", 20),
    ("group-based nutrition intervention", 18),
    ("group based nutrition intervention", 18),
    ("group-based dietary intervention", 18),
    ("group based dietary intervention", 18),
    ("group lifestyle intervention diabetes", 18),
    ("group lifestyle intervention obesity", 18),
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
        _dedupe_preserve_order([*watch_scoring.BONUS_TERMS, *GROUP_VISIT_BONUS_TERMS])
    )
    watch_scoring.NUTMEV_SCOPE_TERMS = tuple(
        _dedupe_preserve_order(
            [*watch_scoring.NUTMEV_SCOPE_TERMS, *GROUP_VISIT_NUTRITION_TERMS]
        )
    )


def apply_group_visit_watch_extensions() -> None:
    for category in (
        "lifestyle_medicine",
        "implementation_behavior",
        "obesity_cardiometabolic",
    ):
        _extend_category_terms(category, GROUP_VISIT_NUTRITION_TERMS)
        _extend_query_context(category, GROUP_VISIT_NUTRITION_TERMS)

    _extend_quick_seed_group(
        "lifestyle_medicine",
        1,
        GROUP_VISIT_NUTRITION_TERMS,
    )
    _extend_quick_seed_group(
        "implementation_behavior",
        2,
        GROUP_VISIT_NUTRITION_TERMS,
    )
    _extend_quick_seed_group(
        "obesity_cardiometabolic",
        0,
        GROUP_VISIT_NUTRITION_TERMS,
    )
    _extend_scoring_terms()
