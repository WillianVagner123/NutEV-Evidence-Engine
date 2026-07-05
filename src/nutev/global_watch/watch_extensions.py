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

MASLD_NUTRITION_CARE_TERMS = [
    "MASLD nutrition",
    "MASLD nutrition care",
    "MASLD dietary intervention",
    "MASLD lifestyle intervention",
    "MASLD weight management",
    "MASLD Mediterranean diet",
    "MASH nutrition",
    "MASH dietary intervention",
    "MASH lifestyle intervention",
    "NAFLD nutrition",
    "NAFLD nutrition care",
    "NAFLD dietary intervention",
    "NAFLD lifestyle intervention",
    "NAFLD weight management",
    "NAFLD Mediterranean diet",
    "NASH nutrition",
    "NASH dietary intervention",
    "NASH lifestyle intervention",
    "steatotic liver disease nutrition",
    "steatotic liver disease dietary intervention",
    "steatotic liver disease lifestyle intervention",
    "hepatic steatosis dietary intervention",
]

MASLD_GUIDANCE_TERMS = [
    "MASLD clinical practice guideline",
    "MASLD practice guidance",
    "MASLD consensus statement",
    "MASH clinical practice guideline",
    "MASH practice guidance",
    "MASH consensus statement",
    "NAFLD clinical practice guideline",
    "NAFLD practice guidance",
    "NAFLD consensus statement",
    "NASH clinical practice guideline",
    "NASH practice guidance",
    "NASH consensus statement",
    "steatotic liver disease guideline",
    "steatotic liver disease practice guidance",
    "metabolic dysfunction-associated steatotic liver disease guideline",
    "metabolic dysfunction associated steatotic liver disease guideline",
]

MASLD_NUTRITION_BONUS_TERMS = [
    ("MASLD clinical practice guideline", 24),
    ("MASLD practice guidance", 22),
    ("MASLD consensus statement", 22),
    ("MASH clinical practice guideline", 24),
    ("MASH practice guidance", 22),
    ("NAFLD clinical practice guideline", 22),
    ("NAFLD practice guidance", 20),
    ("NASH clinical practice guideline", 22),
    ("NASH practice guidance", 20),
    ("steatotic liver disease guideline", 22),
    ("steatotic liver disease practice guidance", 20),
    ("MASLD nutrition care", 18),
    ("MASLD dietary intervention", 18),
    ("MASLD lifestyle intervention", 18),
    ("MASLD Mediterranean diet", 16),
    ("MASH dietary intervention", 18),
    ("NAFLD nutrition care", 16),
    ("NAFLD dietary intervention", 16),
    ("NAFLD lifestyle intervention", 16),
    ("NAFLD Mediterranean diet", 16),
    ("NASH dietary intervention", 16),
    ("steatotic liver disease nutrition", 16),
    ("steatotic liver disease dietary intervention", 16),
    ("hepatic steatosis dietary intervention", 14),
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
                *OBESITY_PHARMACOTHERAPY_BONUS_TERMS,
                *MASLD_NUTRITION_BONUS_TERMS,
            ]
        )
    )
    watch_scoring.NUTMEV_SCOPE_TERMS = tuple(
        _dedupe_preserve_order(
            [
                *watch_scoring.NUTMEV_SCOPE_TERMS,
                *OBESITY_PHARMACOTHERAPY_NUTRITION_TERMS,
                *MASLD_NUTRITION_CARE_TERMS,
                *MASLD_GUIDANCE_TERMS,
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
        [*FOOD_ENVIRONMENT_POLICY_TERMS, *FOOD_ENVIRONMENT_DOCUMENT_TERMS],
    )
    _extend_category_terms(
        "implementation_behavior",
        FOOD_ENVIRONMENT_POLICY_TERMS,
    )
    _extend_category_terms(
        "guidelines_consensus",
        [*FOOD_ENVIRONMENT_DOCUMENT_TERMS, *MASLD_GUIDANCE_TERMS],
    )
    _extend_category_terms(
        "obesity_cardiometabolic",
        [*OBESITY_PHARMACOTHERAPY_NUTRITION_TERMS, *MASLD_NUTRITION_CARE_TERMS],
    )
    _extend_category_terms(
        "diet_patterns",
        MASLD_NUTRITION_CARE_TERMS,
    )
    _extend_quick_seed_group(
        "obesity_cardiometabolic",
        0,
        OBESITY_PHARMACOTHERAPY_NUTRITION_TERMS,
    )
    _extend_quick_seed_group(
        "obesity_cardiometabolic",
        2,
        [*MASLD_NUTRITION_CARE_TERMS, *MASLD_GUIDANCE_TERMS],
    )
    _extend_query_context(
        "obesity_cardiometabolic",
        [*OBESITY_PHARMACOTHERAPY_NUTRITION_TERMS, *MASLD_NUTRITION_CARE_TERMS],
    )
    _extend_query_context(
        "diet_patterns",
        MASLD_NUTRITION_CARE_TERMS,
    )
    _extend_query_context(
        "guidelines_consensus",
        MASLD_GUIDANCE_TERMS,
    )
    _extend_scoring_terms()


apply_watch_taxonomy_extensions()
