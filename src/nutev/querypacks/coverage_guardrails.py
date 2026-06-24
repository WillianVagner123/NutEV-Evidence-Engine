from __future__ import annotations

from collections.abc import Iterable, Mapping


ADHERENCE_PRECISION_TERMS = [
    "dietary adherence",
    "diet adherence",
    "treatment adherence",
    "long-term adherence",
    "long term adherence",
    "dietary compliance",
    "diet compliance",
    "persistence",
    "engagement",
    "retention",
    "attrition",
    "dropout",
    "weight maintenance",
    "dietary maintenance",
    "behavioral maintenance",
    "behavioural maintenance",
    "relapse prevention",
    "dietary self-monitoring",
    "self-management support",
]


class CoverageGap(ValueError):
    """Raised when a required semantic search term is absent from coverage."""


def _flatten_terms(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        terms: list[str] = []
        for nested in value.values():
            terms.extend(_flatten_terms(nested))
        return terms
    if isinstance(value, Iterable):
        terms = []
        for nested in value:
            terms.extend(_flatten_terms(nested))
        return terms
    return []


def normalize_term(term: object) -> str:
    return " ".join(str(term or "").lower().replace("-", " ").split())


def missing_required_terms(
    observed_terms: Iterable[object],
    required_terms: Iterable[str] = ADHERENCE_PRECISION_TERMS,
) -> list[str]:
    observed = {normalize_term(term) for term in observed_terms if normalize_term(term)}
    return [term for term in required_terms if normalize_term(term) not in observed]


def assert_adherence_precision_coverage(keyword_taxonomy: Mapping[str, object]) -> None:
    """Validate that taxonomy search blocks cover adherence/persistence variants.

    This guardrail is intentionally narrow: it checks the terms most likely to
    recover diet-intervention adherence and maintenance papers without adding
    broad off-scope behavior vocabulary.
    """

    implementation_behavior = (
        keyword_taxonomy.get("global", {})
        .get("implementation_behavior", {})
    )
    observed_terms = _flatten_terms(implementation_behavior)
    missing = missing_required_terms(observed_terms)
    if missing:
        raise CoverageGap(
            "Missing adherence precision terms in global.implementation_behavior: "
            + ", ".join(missing)
        )
