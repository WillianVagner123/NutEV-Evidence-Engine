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

CARDIOMETABOLIC_NUTRITION_CARE_TERMS = [
    "medical nutrition therapy obesity",
    "medical nutrition therapy type 2 diabetes",
    "medical nutrition therapy hypertension",
    "medical nutrition therapy dyslipidemia",
    "medical nutrition therapy dyslipidaemia",
    "medical nutrition therapy masld",
    "medical nutrition therapy nafld",
    "cardiometabolic nutrition care",
    "cardiometabolic nutrition pathway",
    "cardiometabolic nutrition protocol",
    "obesity nutrition care pathway",
    "obesity nutrition care protocol",
    "diabetes nutrition care pathway",
    "diabetes nutrition care protocol",
    "hypertension nutrition care pathway",
    "dyslipidemia nutrition care pathway",
    "dyslipidaemia nutrition care pathway",
    "masld nutrition care pathway",
    "nafld nutrition care pathway",
    "dietitian-led cardiometabolic care",
    "dietitian led cardiometabolic care",
    "dietitian-led weight management",
    "dietitian led weight management",
    "dietitian-led diabetes care",
    "dietitian led diabetes care",
]

CARDIOMETABOLIC_NUTRITION_CARE_BONUS_TERMS = [
    ("medical nutrition therapy obesity", 22),
    ("medical nutrition therapy type 2 diabetes", 22),
    ("medical nutrition therapy hypertension", 20),
    ("medical nutrition therapy dyslipidemia", 20),
    ("medical nutrition therapy dyslipidaemia", 20),
    ("medical nutrition therapy masld", 20),
    ("medical nutrition therapy nafld", 20),
    ("cardiometabolic nutrition care", 20),
    ("cardiometabolic nutrition pathway", 22),
    ("cardiometabolic nutrition protocol", 22),
    ("obesity nutrition care pathway", 20),
    ("obesity nutrition care protocol", 20),
    ("diabetes nutrition care pathway", 20),
    ("diabetes nutrition care protocol", 20),
    ("hypertension nutrition care pathway", 18),
    ("dyslipidemia nutrition care pathway", 18),
    ("dyslipidaemia nutrition care pathway", 18),
    ("masld nutrition care pathway", 18),
    ("nafld nutrition care pathway", 18),
    ("dietitian-led cardiometabolic care", 18),
    ("dietitian led cardiometabolic care", 18),
    ("dietitian-led weight management", 18),
    ("dietitian led weight management", 18),
    ("dietitian-led diabetes care", 18),
    ("dietitian led diabetes care", 18),
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
                *SOCIAL_PRESCRIBING_BONUS_TERMS,
                *CARDIOMETABOLIC_NUTRITION_CARE_BONUS_TERMS,
                *OBESITY_PHARMACOTHERAPY_BONUS_TERMS,
            ]
        )
    )
    watch_scoring.NUTMEV_SCOPE_TERMS = tuple(
        _dedupe_preserve_order(
            [
                *watch_scoring.NUTMEV_SCOPE_TERMS,
                *SOCIAL_PRESCRIBING_NUTRITION_TERMS,
                *CARDIOMETABOLIC_NUTRITION_CARE_TERMS,
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
        [
            *FOOD_ENVIRONMENT_POLICY_TERMS,
            *SOCIAL_PRESCRIBING_NUTRITION_TERMS,
            *CARDIOMETABOLIC_NUTRITION_CARE_TERMS,
        ],
    )
    _extend_category_terms(
        "lifestyle_medicine",
        [*SOCIAL_PRESCRIBING_NUTRITION_TERMS, *CARDIOMETABOLIC_NUTRITION_CARE_TERMS],
    )
    _extend_category_terms(
        "guidelines_consensus",
        [*FOOD_ENVIRONMENT_DOCUMENT_TERMS, *CARDIOMETABOLIC_NUTRITION_CARE_TERMS],
    )
    _extend_category_terms(
        "obesity_cardiometabolic",
        [*CARDIOMETABOLIC_NUTRITION_CARE_TERMS, *OBESITY_PHARMACOTHERAPY_NUTRITION_TERMS],
    )
    _extend_quick_seed_group(
        "lifestyle_medicine",
        0,
        CARDIOMETABOLIC_NUTRITION_CARE_TERMS,
    )
    _extend_quick_seed_group(
        "lifestyle_medicine",
        1,
        SOCIAL_PRESCRIBING_NUTRITION_TERMS,
    )
    _extend_quick_seed_group(
        "implementation_behavior",
        1,
        CARDIOMETABOLIC_NUTRITION_CARE_TERMS,
    )
    _extend_quick_seed_group(
        "implementation_behavior",
        2,
        SOCIAL_PRESCRIBING_NUTRITION_TERMS,
    )
    _extend_quick_seed_group(
        "food_literacy_culinary_commensality",
        0,
        SOCIAL_PRESCRIBING_NUTRITION_TERMS,
    )
    _extend_quick_seed_group(
        "obesity_cardiometabolic",
        0,
        CARDIOMETABOLIC_NUTRITION_CARE_TERMS,
    )
    _extend_quick_seed_group(
        "obesity_cardiometabolic",
        0,
        OBESITY_PHARMACOTHERAPY_NUTRITION_TERMS,
    )
    _extend_query_context(
        "lifestyle_medicine",
        [*SOCIAL_PRESCRIBING_NUTRITION_TERMS, *CARDIOMETABOLIC_NUTRITION_CARE_TERMS],
    )
    _extend_query_context(
        "implementation_behavior",
        [*SOCIAL_PRESCRIBING_NUTRITION_TERMS, *CARDIOMETABOLIC_NUTRITION_CARE_TERMS],
    )
    _extend_query_context(
        "food_literacy_culinary_commensality",
        SOCIAL_PRESCRIBING_NUTRITION_TERMS,
    )
    _extend_query_context(
        "obesity_cardiometabolic",
        [*CARDIOMETABOLIC_NUTRITION_CARE_TERMS, *OBESITY_PHARMACOTHERAPY_NUTRITION_TERMS],
    )
    _extend_scoring_terms()


apply_watch_taxonomy_extensions()
