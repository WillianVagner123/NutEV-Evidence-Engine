from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from nutev.global_watch import watch_config

SARCOPENIC_OBESITY_NUTRITION_TERMS = [
    "sarcopenic obesity nutrition",
    "sarcopenic obesity diet",
    "sarcopenic obesity dietary intervention",
    "sarcopenic obesity lifestyle intervention",
    "lean mass preservation weight loss",
    "lean mass preservation obesity",
    "fat-free mass preservation weight loss",
    "fat free mass preservation weight loss",
    "muscle preservation weight loss",
    "muscle mass preservation obesity",
    "body composition change weight loss",
    "body composition changes weight loss",
    "protein adequacy weight loss",
    "protein adequacy obesity",
    "dietary protein weight management",
    "high-protein diet weight maintenance",
    "high protein diet weight maintenance",
    "protein intake anti-obesity medication",
    "protein intake obesity pharmacotherapy",
    "protein intake glp-1",
    "protein intake glp-1 receptor agonist",
]

SARCOPENIC_OBESITY_BONUS_TERMS = [
    ("sarcopenic obesity nutrition", 18),
    ("sarcopenic obesity dietary intervention", 18),
    ("sarcopenic obesity lifestyle intervention", 18),
    ("lean mass preservation weight loss", 18),
    ("lean mass preservation obesity", 18),
    ("fat-free mass preservation weight loss", 18),
    ("fat free mass preservation weight loss", 18),
    ("muscle preservation weight loss", 18),
    ("muscle mass preservation obesity", 18),
    ("body composition change weight loss", 16),
    ("protein adequacy weight loss", 16),
    ("protein adequacy obesity", 16),
    ("dietary protein weight management", 16),
    ("high-protein diet weight maintenance", 16),
    ("high protein diet weight maintenance", 16),
    ("protein intake anti-obesity medication", 16),
    ("protein intake obesity pharmacotherapy", 16),
    ("protein intake glp-1", 16),
    ("protein intake glp-1 receptor agonist", 16),
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
                *SARCOPENIC_OBESITY_BONUS_TERMS,
            ]
        )
    )
    watch_scoring.NUTMEV_SCOPE_TERMS = tuple(
        _dedupe_preserve_order(
            [
                *watch_scoring.NUTMEV_SCOPE_TERMS,
                *SARCOPENIC_OBESITY_NUTRITION_TERMS,
                "lean mass preservation",
                "fat-free mass preservation",
                "fat free mass preservation",
                "muscle preservation",
                "protein adequacy",
                "dietary protein",
                "high-protein diet",
                "high protein diet",
                "body composition change",
                "body composition changes",
            ]
        )
    )


def apply_sarcopenic_obesity_watch_extensions() -> None:
    _extend_category_terms(
        "obesity_cardiometabolic",
        SARCOPENIC_OBESITY_NUTRITION_TERMS,
    )
    _extend_quick_seed_group(
        "obesity_cardiometabolic",
        0,
        SARCOPENIC_OBESITY_NUTRITION_TERMS,
    )
    _extend_query_context(
        "obesity_cardiometabolic",
        SARCOPENIC_OBESITY_NUTRITION_TERMS,
    )
    _extend_scoring_terms()
