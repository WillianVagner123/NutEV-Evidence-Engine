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
    "healthy food retail intervention",
    "choice architecture intervention",
    "food choice architecture",
    "choice architecture for healthy eating",
    "healthy choice architecture",
    "healthy food placement",
    "healthy food placement intervention",
    "healthy default",
    "healthy defaults",
    "healthy default option",
    "healthy default intervention",
    "default option intervention",
    "menu default",
    "healthy checkout",
    "checkout intervention",
    "cafeteria intervention",
    "worksite cafeteria intervention",
    "school food environment intervention",
    "worksite food environment intervention",
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
    "choice architecture intervention",
    "healthy food retail intervention",
    "healthy default intervention",
    "cafeteria intervention",
    "worksite food environment intervention",
]

FOOD_ENVIRONMENT_BONUS_TERMS = [
    ("choice architecture for healthy eating", 16),
    ("healthy food retail intervention", 16),
    ("healthy food placement intervention", 16),
    ("healthy default intervention", 16),
    ("food procurement policy", 14),
    ("healthy food procurement policy", 16),
    ("food service guidelines", 14),
    ("nutrition standards for food service", 16),
    ("school food environment intervention", 16),
    ("worksite food environment intervention", 16),
]

SOCIAL_PRESCRIBING_NUTRITION_TERMS = [
    "nutrition social prescribing",
    "food social prescribing",
    "social prescribing nutrition",
    "social prescribing food",
    "social prescribing dietary intervention",
    "social prescribing healthy eating",
    "social prescribing food insecurity",
    "social prescribing nutrition security",
    "social prescribing link worker nutrition",
    "social prescribing link worker food",
    "link worker nutrition referral",
    "link worker food referral",
    "community connector nutrition referral",
    "community connector food referral",
    "community resource referral nutrition",
    "community resource referral food",
    "community referral nutrition program",
    "community referral food program",
]

SOCIAL_PRESCRIBING_BONUS_TERMS = [
    ("nutrition social prescribing", 20),
    ("food social prescribing", 20),
    ("social prescribing nutrition", 18),
    ("social prescribing food", 18),
    ("social prescribing dietary intervention", 20),
    ("social prescribing healthy eating", 18),
    ("social prescribing food insecurity", 18),
    ("social prescribing nutrition security", 20),
    ("social prescribing link worker nutrition", 18),
    ("social prescribing link worker food", 18),
    ("link worker nutrition referral", 16),
    ("link worker food referral", 16),
    ("community connector nutrition referral", 16),
    ("community connector food referral", 16),
    ("community resource referral nutrition", 16),
    ("community resource referral food", 16),
    ("community referral nutrition program", 16),
    ("community referral food program", 16),
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
    "semaglutide nutrition",
    "semaglutide nutrition care",
    "semaglutide dietary counseling",
    "semaglutide dietary counselling",
    "tirzepatide nutrition",
    "tirzepatide nutrition care",
    "tirzepatide dietary counseling",
    "tirzepatide dietary counselling",
    "incretin therapy nutrition care",
    "incretin therapy dietary counseling",
    "incretin therapy dietary counselling",
    "incretin-based therapy nutrition",
    "incretin based therapy nutrition",
    "incretin-based obesity treatment nutrition",
    "incretin based obesity treatment nutrition",
    "lean mass preservation glp-1",
    "lean mass preservation semaglutide",
    "lean mass preservation tirzepatide",
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
    ("semaglutide nutrition", 18),
    ("semaglutide nutrition care", 20),
    ("semaglutide dietary counseling", 18),
    ("semaglutide dietary counselling", 18),
    ("tirzepatide nutrition", 18),
    ("tirzepatide nutrition care", 20),
    ("tirzepatide dietary counseling", 18),
    ("tirzepatide dietary counselling", 18),
    ("incretin therapy nutrition care", 18),
    ("incretin therapy dietary counseling", 16),
    ("incretin therapy dietary counselling", 16),
    ("incretin-based therapy nutrition", 18),
    ("incretin based therapy nutrition", 18),
    ("incretin-based obesity treatment nutrition", 20),
    ("incretin based obesity treatment nutrition", 20),
    ("lean mass preservation glp-1", 18),
    ("lean mass preservation semaglutide", 18),
    ("lean mass preservation tirzepatide", 18),
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
                *FOOD_ENVIRONMENT_BONUS_TERMS,
                *SOCIAL_PRESCRIBING_BONUS_TERMS,
                *OBESITY_PHARMACOTHERAPY_BONUS_TERMS,
            ]
        )
    )
    watch_scoring.NUTMEV_SCOPE_TERMS = tuple(
        _dedupe_preserve_order(
            [
                *watch_scoring.NUTMEV_SCOPE_TERMS,
                *FOOD_ENVIRONMENT_POLICY_TERMS,
                *FOOD_ENVIRONMENT_DOCUMENT_TERMS,
                *SOCIAL_PRESCRIBING_NUTRITION_TERMS,
                *OBESITY_PHARMACOTHERAPY_NUTRITION_TERMS,
            ]
        )
    )


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
        [
            *FOOD_ENVIRONMENT_POLICY_TERMS,
            *FOOD_ENVIRONMENT_DOCUMENT_TERMS,
            *SOCIAL_PRESCRIBING_NUTRITION_TERMS,
        ],
    )
    _extend_category_terms(
        "implementation_behavior",
        [*FOOD_ENVIRONMENT_POLICY_TERMS, *SOCIAL_PRESCRIBING_NUTRITION_TERMS],
    )
    _extend_category_terms(
        "lifestyle_medicine",
        SOCIAL_PRESCRIBING_NUTRITION_TERMS,
    )
    _extend_category_terms(
        "guidelines_consensus",
        FOOD_ENVIRONMENT_DOCUMENT_TERMS,
    )
    _extend_category_terms(
        "obesity_cardiometabolic",
        OBESITY_PHARMACOTHERAPY_NUTRITION_TERMS,
    )
    _extend_quick_seed_group(
        "lifestyle_medicine",
        1,
        SOCIAL_PRESCRIBING_NUTRITION_TERMS,
    )
    _extend_quick_seed_group(
        "implementation_behavior",
        2,
        SOCIAL_PRESCRIBING_NUTRITION_TERMS,
    )
    _extend_quick_seed_group(
        "food_literacy_culinary_commensality",
        0,
        [*FOOD_ENVIRONMENT_POLICY_TERMS, *SOCIAL_PRESCRIBING_NUTRITION_TERMS],
    )
    _extend_quick_seed_group(
        "obesity_cardiometabolic",
        0,
        OBESITY_PHARMACOTHERAPY_NUTRITION_TERMS,
    )
    _extend_query_context(
        "lifestyle_medicine",
        SOCIAL_PRESCRIBING_NUTRITION_TERMS,
    )
    _extend_query_context(
        "implementation_behavior",
        [*FOOD_ENVIRONMENT_POLICY_TERMS, *SOCIAL_PRESCRIBING_NUTRITION_TERMS],
    )
    _extend_query_context(
        "food_literacy_culinary_commensality",
        [*FOOD_ENVIRONMENT_POLICY_TERMS, *SOCIAL_PRESCRIBING_NUTRITION_TERMS],
    )
    _extend_query_context(
        "guidelines_consensus",
        FOOD_ENVIRONMENT_DOCUMENT_TERMS,
    )
    _extend_query_context(
        "obesity_cardiometabolic",
        OBESITY_PHARMACOTHERAPY_NUTRITION_TERMS,
    )
    _extend_scoring_terms()


apply_watch_taxonomy_extensions()
