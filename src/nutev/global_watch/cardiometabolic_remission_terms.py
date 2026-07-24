from __future__ import annotations

from collections.abc import Iterable


DIABETES_REMISSION_MAINTENANCE_TERMS: tuple[str, ...] = (
    "type 2 diabetes remission",
    "remission of type 2 diabetes",
    "diabetes remission",
    "diabetes reversal",
    "glycemic remission",
    "glycaemic remission",
    "diet-induced diabetes remission",
    "diet induced diabetes remission",
    "lifestyle-induced diabetes remission",
    "lifestyle induced diabetes remission",
    "remission maintenance",
    "diabetes remission maintenance",
    "weight loss maintenance",
    "long-term weight loss maintenance",
    "long term weight loss maintenance",
    "weight regain prevention",
    "weight regain management",
    "dietary maintenance",
    "behavioral maintenance",
    "relapse prevention",
    "dietary self-monitoring",
    "dietary self-regulation",
)


def dedupe_terms(terms: Iterable[str]) -> tuple[str, ...]:
    """Return terms in first-seen order with case-insensitive duplicates removed."""
    seen: set[str] = set()
    out: list[str] = []
    for term in terms:
        value = str(term).strip()
        if not value:
            continue
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return tuple(out)


def cardiometabolic_remission_terms(extra_terms: Iterable[str] = ()) -> tuple[str, ...]:
    return dedupe_terms((*DIABETES_REMISSION_MAINTENANCE_TERMS, *extra_terms))
