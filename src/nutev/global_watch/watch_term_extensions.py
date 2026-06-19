from __future__ import annotations

from collections.abc import MutableSequence

SOCIAL_PRESCRIBING_ACCESS_TERMS = [
    "social prescribing",
    "social prescribing program",
    "social prescribing programme",
    "social prescribing link worker",
    "nutrition social prescribing",
    "food social prescribing",
    "screen and refer",
    "screen-and-refer",
    "screen and intervene",
    "screen-and-intervene",
    "screening and referral",
    "closed-loop referral",
    "closed loop referral",
    "community referral",
    "community referrals",
    "community resource referral",
    "community resource referrals",
    "community resource navigation",
    "food resource navigation",
    "link worker",
    "link workers",
    "community connector",
    "community connectors",
    "patient navigation",
    "patient navigator",
    "patient navigators",
    "care navigation",
    "care navigator",
    "care navigators",
    "food is medicine referral",
    "food as medicine referral",
    "produce prescription referral",
    "medically tailored food referral",
    "nutrition security referral",
]

_CONTEXT_CATEGORIES = (
    "lifestyle_medicine",
    "implementation_behavior",
    "food_literacy_culinary_commensality",
)


def _extend_unique(target: MutableSequence[str], additions: list[str]) -> None:
    seen = {str(term).strip().lower() for term in target if str(term).strip()}
    for term in additions:
        value = str(term).strip()
        if not value:
            continue
        lowered = value.lower()
        if lowered in seen:
            continue
        target.append(value)
        seen.add(lowered)


def install_watch_query_extensions() -> None:
    from nutev.global_watch import watch_query_builder as builder

    _extend_unique(builder.FOOD_AS_MEDICINE_ACCESS_TERMS, SOCIAL_PRESCRIBING_ACCESS_TERMS)
    for category in _CONTEXT_CATEGORIES:
        context_terms = builder.CATEGORY_CONTEXT_TERMS.setdefault(category, [])
        _extend_unique(context_terms, SOCIAL_PRESCRIBING_ACCESS_TERMS)
