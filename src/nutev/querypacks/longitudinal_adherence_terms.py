from __future__ import annotations

from collections.abc import Iterable


LONGITUDINAL_ADHERENCE_FOCUS_TERMS = [
    "long-term dietary adherence",
    "long term dietary adherence",
    "dietary adherence maintenance",
    "adherence maintenance",
    "persistence with lifestyle intervention",
    "lifestyle intervention persistence",
    "intervention engagement",
    "intervention retention",
    "weight loss maintenance",
    "long-term weight loss maintenance",
    "long term weight loss maintenance",
    "weight regain prevention",
    "weight regain management",
    "relapse prevention",
    "lapse management",
    "dietary lapse",
    "dietary lapses",
    "habit formation",
    "maintenance of behavior change",
    "maintenance of behaviour change",
    "behavioral maintenance",
    "behavioural maintenance",
    "self-monitoring",
    "dietary self-monitoring",
    "dietary self-regulation",
    "dietary self regulation",
    "eating self-regulation",
    "self-regulation of eating",
]

METABOLIC_REMISSION_MAINTENANCE_TERMS = [
    "diabetes remission maintenance",
    "type 2 diabetes remission maintenance",
    "remission maintenance",
    "maintenance of diabetes remission",
    "maintenance of type 2 diabetes remission",
    "diet-induced diabetes remission",
    "diet induced diabetes remission",
    "lifestyle-induced diabetes remission",
    "lifestyle induced diabetes remission",
    "diabetes remission relapse",
    "type 2 diabetes remission relapse",
    "diabetes remission recurrence",
    "weight loss maintenance after diabetes remission",
]

LONGITUDINAL_ADHERENCE_DOCUMENT_TERMS = [
    "adherence intervention",
    "dietary adherence intervention",
    "maintenance intervention",
    "maintenance trial",
    "weight loss maintenance trial",
    "weight loss maintenance systematic review",
    "weight regain prevention trial",
    "relapse prevention intervention",
    "diabetes remission maintenance trial",
    "diabetes remission maintenance study",
    "type 2 diabetes remission maintenance trial",
    "longitudinal adherence study",
    "long-term follow-up",
    "long term follow-up",
    "long-term follow up",
    "long term follow up",
]


def uniq_terms(groups: Iterable[Iterable[str]]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for group in groups:
        for term in group:
            value = str(term).strip()
            if not value:
                continue
            key = value.lower()
            if key in seen:
                continue
            seen.add(key)
            output.append(value)
    return output


def longitudinal_adherence_terms() -> list[str]:
    return uniq_terms(
        [
            LONGITUDINAL_ADHERENCE_FOCUS_TERMS,
            METABOLIC_REMISSION_MAINTENANCE_TERMS,
        ]
    )


def longitudinal_adherence_document_terms() -> list[str]:
    return uniq_terms([LONGITUDINAL_ADHERENCE_DOCUMENT_TERMS])
