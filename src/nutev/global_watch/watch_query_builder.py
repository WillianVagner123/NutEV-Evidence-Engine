from __future__ import annotations

from collections.abc import Iterable

from nutev.engine.ids import make_document_id
from nutev.global_watch.watch_config import MODE_LIMITS, WATCH_CATEGORIES

BASE_CONTEXT_TERMS = [
    "nutrition",
    "diet",
    "obesity",
    "cardiometabolic",
]

CATEGORY_CONTEXT_TERMS = {
    "guidelines_consensus": [
        "dietary guideline",
        "dietary pattern",
        "lifestyle medicine",
    ],
    "lifestyle_medicine": [
        "food literacy",
        "culinary medicine",
        "meal planning",
    ],
    "obesity_cardiometabolic": [
        "dietary pattern",
        "lifestyle medicine",
        "implementation",
        "adherence",
    ],
    "diet_patterns": [
        "type 2 diabetes",
        "hypertension",
        "implementation",
        "adherence",
    ],
    "implementation_behavior": [
        "lifestyle medicine",
        "food literacy",
        "culinary medicine",
    ],
    "food_literacy_culinary_commensality": [
        "lifestyle medicine",
        "behavior change",
        "adherence",
    ],
    "frameworks_instruments": [
        "lifestyle medicine",
        "food literacy",
        "culinary medicine",
        "commensality",
    ],
}

HIGH_PRIORITY_MARKERS = (
    "guideline",
    "consensus",
    "statement",
    "recommendation",
)


def _dedupe_terms(terms: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    unique_terms: list[str] = []
    for term in terms:
        value = str(term).strip()
        if not value:
            continue
        lowered = value.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique_terms.append(value)
    return unique_terms


def _quote_term(term: str) -> str:
    return f'"{term.strip()}"'


def _or_clause(terms: Iterable[str]) -> str:
    quoted_terms = [_quote_term(term) for term in _dedupe_terms(terms)]
    if not quoted_terms:
        return ""
    if len(quoted_terms) == 1:
        return quoted_terms[0]
    return "(" + " OR ".join(quoted_terms) + ")"


def _build_context_terms(category: str) -> list[str]:
    return _dedupe_terms(
        [
            *BASE_CONTEXT_TERMS,
            *CATEGORY_CONTEXT_TERMS.get(category, []),
        ]
    )


def _priority_for_term(term: str) -> int:
    lowered = term.lower()
    return 1 if any(marker in lowered for marker in HIGH_PRIORITY_MARKERS) else 2


def build_watch_queries(
    categories: list[str] | None,
    since_days: int,
    mode: str,
) -> list[dict[str, object]]:
    selected_categories = categories or list(WATCH_CATEGORIES.keys())
    limit = MODE_LIMITS.get(mode, 6)
    queries: list[dict[str, object]] = []

    for category in selected_categories:
        context_clause = _or_clause(_build_context_terms(category))
        for term in WATCH_CATEGORIES.get(category, [])[:limit]:
            term_clause = _quote_term(term)
            query = f"({term_clause})"
            if context_clause:
                query = f"{query} AND {context_clause}"
            queries.append(
                {
                    "query_id": make_document_id(
                        {"title": query, "provider": "watch", "year": since_days}
                    ),
                    "category": category,
                    "query": query,
                    "provider_hint": "pubmed",
                    "priority": _priority_for_term(term),
                    "since_days": since_days,
                }
            )
    return queries
