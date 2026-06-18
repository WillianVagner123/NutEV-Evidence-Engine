from __future__ import annotations

from collections.abc import Iterable

GROUP_DELIVERY_TERMS = [
    "shared medical appointment",
    "shared medical appointments",
    "group medical visit",
    "group medical visits",
    "group visit",
    "group visits",
    "shared visit",
    "shared visits",
    "group-based lifestyle intervention",
    "group based lifestyle intervention",
    "group lifestyle intervention",
    "group-based nutrition intervention",
    "group based nutrition intervention",
    "group nutrition intervention",
    "group nutrition counseling",
    "group nutrition counselling",
    "group dietary counseling",
    "group dietary counselling",
    "group medical nutrition therapy",
    "group diabetes prevention program",
    "group diabetes prevention programme",
]

GROUP_DELIVERY_DOCUMENT_TERMS = [
    "shared medical appointment trial",
    "shared medical appointments trial",
    "group medical visit trial",
    "group medical visits trial",
    "group-based lifestyle intervention trial",
    "group based lifestyle intervention trial",
    "group nutrition intervention trial",
    "group medical nutrition therapy trial",
    "shared medical appointment implementation",
    "group visit implementation",
    "group-based lifestyle intervention implementation",
    "group nutrition counseling implementation",
    "group nutrition counselling implementation",
]

GROUP_DELIVERY_NUTRITION_ANCHORS = [
    "nutrition",
    "diet",
    "dietary",
    "medical nutrition therapy",
    "nutrition counseling",
    "nutrition counselling",
    "dietary counseling",
    "dietary counselling",
    "lifestyle medicine",
    "lifestyle intervention",
    "diabetes prevention program",
    "diabetes prevention programme",
    "obesity",
    "type 2 diabetes",
    "cardiometabolic risk",
]


def uniq_terms(terms: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for term in terms:
        value = str(term).strip()
        if not value:
            continue
        lowered = value.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        out.append(value)
    return out


def group_delivery_terms() -> list[str]:
    return uniq_terms(GROUP_DELIVERY_TERMS)


def group_delivery_document_terms() -> list[str]:
    return uniq_terms(GROUP_DELIVERY_DOCUMENT_TERMS)


def nutrition_anchored_group_delivery_terms() -> list[str]:
    return uniq_terms([*GROUP_DELIVERY_TERMS, *GROUP_DELIVERY_NUTRITION_ANCHORS])
