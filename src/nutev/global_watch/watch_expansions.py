from __future__ import annotations

from collections.abc import MutableMapping, Sequence
from typing import Any

PERSONALIZED_NUTRITION_PHENOTYPE_GROUPS: tuple[tuple[str, ...], ...] = (
    (
        "precision nutrition glycemic response",
        "precision nutrition glycaemic response",
        "personalized nutrition postprandial glucose",
        "personalised nutrition postprandial glucose",
        "tailored dietary advice glycemic response",
        "tailored dietary advice glycaemic response",
        "continuous glucose monitoring dietary advice",
        "precision nutrition insulin resistance",
    ),
    (
        "precision nutrition implementation type 2 diabetes",
        "personalized nutrition implementation obesity",
        "personalised nutrition implementation obesity",
        "personalized dietary intervention type 2 diabetes",
        "personalised dietary intervention type 2 diabetes",
        "personalized dietary intervention cardiometabolic risk",
        "personalised dietary intervention cardiometabolic risk",
        "precision nutrition adherence",
        "tailored dietary intervention adherence",
    ),
    (
        "glycemic response",
        "glycaemic response",
        "postprandial glucose",
        "post-prandial glucose",
        "continuous glucose monitoring",
        "cgm-guided nutrition",
        "glucose-guided dietary advice",
    ),
)


def _extend_unique(target: list[Any], terms: Sequence[str]) -> None:
    existing = {str(term).lower() for term in target}
    for term in terms:
        if term.lower() not in existing:
            target.append(term)
            existing.add(term.lower())


def apply_watch_expansions(watch_categories: MutableMapping[str, list[Any]]) -> None:
    """Apply deterministic NutMEV watch-term expansions in-place."""
    category = watch_categories.get("personalized_nutrition")
    if not category:
        return

    for group_index, terms in enumerate(PERSONALIZED_NUTRITION_PHENOTYPE_GROUPS):
        if group_index >= len(category):
            category.append([])
        group = category[group_index]
        if isinstance(group, list):
            _extend_unique(group, terms)
        else:
            category[group_index] = [group, *terms]
