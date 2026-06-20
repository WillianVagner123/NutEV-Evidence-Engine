from __future__ import annotations

from collections.abc import Mapping, Sequence

from nutev.querypacks.semantic_blocks import semantic_terms

CoverageSpec = Mapping[str, Sequence[str]]

NUTEV_REQUIRED_SEMANTIC_TERMS: dict[str, tuple[str, ...]] = {
    "busca1": (
        "dietary pattern",
        "food is medicine",
        "food literacy",
        "commensality",
        "implementation science",
    ),
    "busca2a": (
        "cardiometabolic risk",
        "prediabetes",
        "masld",
        "nutrition care pathway",
        "implementation science",
    ),
    "busca2b": (
        "dietary adherence",
        "behavior change technique",
        "food prescription program",
        "medically tailored meals",
        "implementation outcomes",
    ),
    "artigo3_framework": (
        "food literacy",
        "culinary medicine",
        "commensality",
        "food agency",
        "nutrition care pathway",
    ),
}


def missing_required_semantic_terms(
    spec: CoverageSpec = NUTEV_REQUIRED_SEMANTIC_TERMS,
    *,
    min_priority: int = 1,
) -> dict[str, list[str]]:
    """Return required semantic terms that are absent from each workstream.

    This is a lightweight QA guard for query expansion: it does not decide
    relevance, but it makes critical NutMEV concepts auditable and testable.
    """

    missing: dict[str, list[str]] = {}
    for workstream, required_terms in spec.items():
        available_terms = {
            term.lower() for term in semantic_terms(workstream, min_priority=min_priority)
        }
        missing_terms = [
            term for term in required_terms if term.lower() not in available_terms
        ]
        if missing_terms:
            missing[workstream] = missing_terms
    return missing
