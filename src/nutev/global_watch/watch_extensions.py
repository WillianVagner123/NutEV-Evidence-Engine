from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from nutev.global_watch import watch_config

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

METABOLIC_MAINTENANCE_TERMS = [
    "type 2 diabetes remission",
    "remission of type 2 diabetes",
    "diabetes remission",
    "diabetes reversal",
    "glycemic remission",
    "glycaemic remission",
    "weight loss maintenance",
    "long-term weight loss maintenance",
    "long term weight loss maintenance",
    "weight maintenance",
    "weight regain prevention",
    "weight regain management",
    "relapse prevention",
    "lapse management",
    "behavioral maintenance",
    "behavioural maintenance",
    "dietary maintenance",
    "dietary self-monitoring",
    "dietary self-regulation",
]

METABOLIC_MAINTENANCE_NUTRITION_TERMS = [
    "nutrition care for diabetes remission",
    "nutrition care for weight maintenance",
    "medical nutrition therapy diabetes remission",
    "medical nutrition therapy weight maintenance",
    "dietitian-led remission",
    "dietitian led remission",
    "dietitian-led weight maintenance",
    "dietitian led weight maintenance",
    "dietary counseling weight maintenance",
    "dietary counselling weight maintenance",
    "nutrition counseling weight maintenance",
    "nutrition counselling weight maintenance",
]

METABOLIC_MAINTENANCE_DOCUMENT_TERMS = [
    "diabetes remission guideline",
    "diabetes remission consensus",
    "diabetes remission consensus report",
    "type 2 diabetes remission guideline",
    "type 2 diabetes remission consensus",
    "weight loss maintenance guideline",
    "weight loss maintenance systematic review",
    "weight regain prevention trial",
    "weight regain prevention systematic review",
]

METABOLIC_MAINTENANCE_BONUS_TERMS = [
    ("type 2 diabetes remission", 20),
    ("remission of type 2 diabetes", 20),
    ("diabetes remission", 20),
    ("diabetes reversal", 18),
    ("glycemic remission", 18),
    ("glycaemic remission", 18),
    ("nutrition care for diabetes remission", 22),
    ("medical nutrition therapy diabetes remission", 22),
    ("dietitian-led remission", 18),
    ("dietitian led remission", 18),
    ("weight loss maintenance", 16),
    ("long-term weight loss maintenance", 18),
    ("long term weight loss maintenance", 18),
    ("weight regain prevention", 16),
    ("relapse prevention", 14),
    ("dietary self-monitoring", 14),
    ("dietary self-regulation", 14),
]

OBESITY_PHARMACOTHERAPY_NUTRITION_TERMS = [
    "anti-obesity medication nutrition",
    "anti-obesity medication nutrition care",
    "anti-obesity medication dietary counseling",
    "anti-obesity medication dietary counselling",
    "obesity pharmacotherapy nutrition care",
    "obesity pharmacotherapy dietary counseling",
    "obesity pharmacotherapy dietary counselling",
    "glp-1 nutrition",
    "glp-1 dietary counseling",
    "glp-1 dietary counselling",
    "glp-1 receptor agonist nutrition",
    "glp-1 receptor agonist nutrition care",
    "glp-1 receptor agonist dietary counseling",
    "glp-1 receptor agonist dietary counselling",
    "incretin therapy nutrition care",
    "incretin therapy dietary counseling",
    "incretin therapy dietary counselling",
]

OBESITY_PHARMACOTHERAPY_BONUS_TERMS = [
    ("anti-obesity medication nutrition", 18),
    ("anti-obesity medication nutrition care", 20),
    ("anti-obesity medication dietary counseling", 18),
    ("anti-obesity medication dietary counselling", 18),
    ("obesity pharmacotherapy nutrition care", 20),
    ("obesity pharmacotherapy dietary counseling", 18),
    ("obesity pharmacotherapy dietary counselling", 18),
    ("glp-1 nutrition", 16),
    ("glp-1 dietary counseling", 16),
    ("glp-1 dietary counselling", 16),
    ("glp-1 receptor agonist nutrition", 18),
    ("glp-1 receptor agonist nutrition care", 20),
    ("glp-1 receptor agonist dietary counseling", 18),
    ("glp-1 receptor agonist dietary counselling", 18),
    ("incretin therapy nutrition care", 18),
    ("incretin therapy dietary counseling", 16),
    ("incretin therapy dietary counselling", 16),
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
                *METABOLIC_MAINTENANCE_BONUS_TERMS,
                *OBESITY_PHARMACOTHERAPY_BONUS_TERMS,
            ]
        )
    )
    watch_scoring.NUTMEV_SCOPE_TERMS = tuple(
        _dedupe_preserve_order(
            [
                *watch_scoring.NUTMEV_SCOPE_TERMS,
                *METABOLIC_MAINTENANCE_TERMS,
                *METABOLIC_MAINTENANCE_NUTRITION_TERMS,
                *OBESITY_PHARMACOTHERAPY_NUTRITION_TERMS,
            ]
        )
    )


def apply_watch_taxonomy_extensions() -> None:
    _extend_seed_group(
        "personalized_nutrition",
        0,
        [
            *PERSONALIZED_NUTRITION_CARDIOMETABOLIC_TERMS,
            *METABOLIC_MAINTENANCE_NUTRITION_TERMS,
        ],
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
        [*FOOD_ENVIRONMENT_POLICY_TERMS, *METABOLIC_MAINTENANCE_TERMS],
    )
    _extend_category_terms(
        "guidelines_consensus",
        [*FOOD_ENVIRONMENT_DOCUMENT_TERMS, *METABOLIC_MAINTENANCE_DOCUMENT_TERMS],
    )
    _extend_category_terms(
        "obesity_cardiometabolic",
        [*METABOLIC_MAINTENANCE_TERMS, *OBESITY_PHARMACOTHERAPY_NUTRITION_TERMS],
    )
    _extend_quick_seed_group(
        "obesity_cardiometabolic",
        0,
        [*METABOLIC_MAINTENANCE_TERMS, *OBESITY_PHARMACOTHERAPY_NUTRITION_TERMS],
    )
    _extend_quick_seed_group(
        "implementation_behavior",
        0,
        METABOLIC_MAINTENANCE_TERMS,
    )
    _extend_query_context(
        "obesity_cardiometabolic",
        [*METABOLIC_MAINTENANCE_TERMS, *OBESITY_PHARMACOTHERAPY_NUTRITION_TERMS],
    )
    _extend_query_context(
        "implementation_behavior",
        METABOLIC_MAINTENANCE_TERMS,
    )
    _extend_scoring_terms()


apply_watch_taxonomy_extensions()
