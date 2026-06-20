from __future__ import annotations

from collections.abc import MutableMapping

METABOLIC_REMISSION_QUERY_TERMS = [
    "type 2 diabetes remission",
    "diabetes remission",
    "remission of type 2 diabetes",
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
]

METABOLIC_REMISSION_INTERVENTION_TERMS = [
    "diabetes remission intervention",
    "type 2 diabetes remission intervention",
    "diabetes remission program",
    "diabetes remission programme",
    "dietitian-led remission",
    "dietitian led remission",
    "nutrition care for diabetes remission",
    "nutrition care for weight maintenance",
    "weight maintenance intervention",
    "weight loss maintenance intervention",
    "weight regain prevention intervention",
]


def _extend_unique(values: list[str], additions: list[str]) -> list[str]:
    seen = {str(value).strip().lower() for value in values if str(value).strip()}
    output = list(values)
    for term in additions:
        value = str(term).strip()
        if not value or value.lower() in seen:
            continue
        seen.add(value.lower())
        output.append(value)
    return output


def _extend_seed_group(
    groups: MutableMapping[str, list[list[str]]],
    category: str,
    index: int,
    additions: list[str],
) -> None:
    bucket = groups.get(category)
    if bucket is None or len(bucket) <= index:
        return
    bucket[index] = _extend_unique(bucket[index], additions)


def apply_watch_query_extensions() -> None:
    from nutev.global_watch import watch_query_builder as builder

    remission_terms = METABOLIC_REMISSION_QUERY_TERMS
    intervention_terms = METABOLIC_REMISSION_INTERVENTION_TERMS

    builder.CATEGORY_CONTEXT_TERMS["obesity_cardiometabolic"] = _extend_unique(
        builder.CATEGORY_CONTEXT_TERMS.get("obesity_cardiometabolic", []),
        remission_terms,
    )
    builder.CATEGORY_CONTEXT_TERMS["implementation_behavior"] = _extend_unique(
        builder.CATEGORY_CONTEXT_TERMS.get("implementation_behavior", []),
        remission_terms + intervention_terms,
    )
    builder.CATEGORY_CONTEXT_TERMS["lifestyle_medicine"] = _extend_unique(
        builder.CATEGORY_CONTEXT_TERMS.get("lifestyle_medicine", []),
        intervention_terms,
    )

    _extend_seed_group(
        builder.QUICK_MODE_SEED_GROUPS,
        "obesity_cardiometabolic",
        1,
        remission_terms[:6],
    )
    _extend_seed_group(
        builder.QUICK_MODE_SEED_GROUPS,
        "implementation_behavior",
        0,
        remission_terms[10:],
    )
    _extend_seed_group(
        builder.QUICK_MODE_SEED_GROUPS,
        "implementation_behavior",
        2,
        intervention_terms,
    )
    _extend_seed_group(
        builder.QUICK_MODE_SEED_GROUPS,
        "lifestyle_medicine",
        1,
        intervention_terms[:4],
    )
