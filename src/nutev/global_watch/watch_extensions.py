from __future__ import annotations

from collections.abc import MutableMapping, Sequence
from typing import Any

from nutev.global_watch import watch_config, watch_query_builder

PERSONALIZED_NUTRITION_CARDIOMETABOLIC_TERMS = [
    "personalized nutrition diabetes remission",
    "personalised nutrition diabetes remission",
    "precision nutrition diabetes remission",
    "tailored dietary intervention diabetes remission",
    "individualized dietary intervention diabetes remission",
    "individualised dietary intervention diabetes remission",
    "personalized nutrition weight maintenance",
    "personalised nutrition weight maintenance",
    "precision nutrition weight maintenance",
    "tailored dietary intervention weight maintenance",
    "personalized nutrition weight regain prevention",
    "personalised nutrition weight regain prevention",
    "precision nutrition weight regain prevention",
]

PERSONALIZED_NUTRITION_IMPLEMENTATION_TERMS = [
    "personalized nutrition adherence",
    "personalised nutrition adherence",
    "precision nutrition adherence",
    "tailored dietary advice adherence",
    "personalized meal planning adherence",
    "personalised meal planning adherence",
    "individualized meal plan adherence",
    "individualised meal plan adherence",
]

FOOD_ENVIRONMENT_POLICY_TERMS = [
    "food service guidelines",
    "healthy food service guidelines",
    "nutrition standards for food service",
    "institutional food procurement",
    "public food procurement",
    "healthy food procurement policy",
    "food procurement policy",
    "healthy food retail policy",
    "choice architecture intervention",
    "healthy choice architecture",
    "healthy default",
    "healthy defaults",
    "food affordability policy",
    "healthy food affordability policy",
]

FOOD_ENVIRONMENT_DOCUMENT_TERMS = [
    "food service guideline",
    "food service guidelines",
    "nutrition standards guideline",
    "procurement guideline",
    "procurement standards",
    "food procurement standards",
    "healthy food procurement standards",
    "food environment policy",
    "food environment policy evaluation",
    "institutional food policy",
    "school food service guideline",
    "worksite food service guideline",
]

OBESITY_BODY_COMPOSITION_NUTRITION_TERMS = [
    "sarcopenic obesity",
    "sarcopenic overweight",
    "body composition",
    "body composition change",
    "body composition changes",
    "muscle preservation",
    "lean mass preservation",
    "fat-free mass preservation",
    "fat free mass preservation",
    "protein intake",
    "dietary protein",
    "protein adequacy",
    "protein distribution",
    "protein quality",
    "high-protein diet",
    "high protein diet",
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


def _extend_seed_group(category: str, group_index: int, terms: Sequence[str]) -> None:
    groups = watch_config.WATCH_CATEGORIES.get(category)
    if not isinstance(groups, list) or group_index >= len(groups):
        return
    group = groups[group_index]
    if not isinstance(group, list):
        return
    group[:] = _dedupe_preserve_order([*group, *terms])


def _extend_category_terms(category: str, terms: Sequence[str]) -> None:
    category_terms = watch_config.WATCH_CATEGORIES.get(category)
    if not isinstance(category_terms, list):
        return
    if any(isinstance(term, list) for term in category_terms):
        return
    category_terms[:] = _dedupe_preserve_order([*category_terms, *terms])


def _extend_query_context_terms(category: str, terms: Sequence[str]) -> None:
    context_terms = watch_query_builder.CATEGORY_CONTEXT_TERMS.get(category)
    if not isinstance(context_terms, list):
        return
    context_terms[:] = _dedupe_preserve_order([*context_terms, *terms])


def _extend_query_seed_group(
    seed_groups: MutableMapping[str, list[list[str]]],
    category: str,
    group_index: int,
    terms: Sequence[str],
) -> None:
    groups = seed_groups.get(category)
    if not isinstance(groups, list) or group_index >= len(groups):
        return
    group = groups[group_index]
    if not isinstance(group, list):
        return
    group[:] = _dedupe_preserve_order([*group, *terms])


def apply_watch_taxonomy_extensions() -> None:
    _extend_seed_group(
        "personalized_nutrition",
        0,
        PERSONALIZED_NUTRITION_CARDIOMETABOLIC_TERMS,
    )
    _extend_seed_group(
        "personalized_nutrition",
        1,
        PERSONALIZED_NUTRITION_IMPLEMENTATION_TERMS,
    )
    _extend_category_terms(
        "food_literacy_culinary_commensality",
        [*FOOD_ENVIRONMENT_POLICY_TERMS, *FOOD_ENVIRONMENT_DOCUMENT_TERMS],
    )
    _extend_category_terms(
        "implementation_behavior",
        FOOD_ENVIRONMENT_POLICY_TERMS,
    )
    _extend_category_terms(
        "guidelines_consensus",
        FOOD_ENVIRONMENT_DOCUMENT_TERMS,
    )
    _extend_category_terms(
        "obesity_cardiometabolic",
        OBESITY_BODY_COMPOSITION_NUTRITION_TERMS,
    )
    _extend_query_context_terms(
        "obesity_cardiometabolic",
        OBESITY_BODY_COMPOSITION_NUTRITION_TERMS,
    )
    _extend_query_seed_group(
        watch_query_builder.QUICK_MODE_SEED_GROUPS,
        "obesity_cardiometabolic",
        0,
        OBESITY_BODY_COMPOSITION_NUTRITION_TERMS,
    )


apply_watch_taxonomy_extensions()
