from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES
from nutev.global_watch.watch_query_builder import build_watch_queries


def _flatten_terms(values: list[object]) -> list[str]:
    terms: list[str] = []
    for value in values:
        if isinstance(value, list):
            terms.extend(str(item) for item in value)
        else:
            terms.append(str(value))
    return terms


def test_personalized_nutrition_category_has_cardio_metabolic_anchors() -> None:
    category_terms = WATCH_CATEGORIES["personalized_nutrition"]
    flattened_terms = _flatten_terms(category_terms)

    assert "precision nutrition type 2 diabetes" in flattened_terms
    assert "tailored dietary advice cardiometabolic risk" in flattened_terms
    assert "tailored dietary intervention obesity" in flattened_terms


def test_personalized_nutrition_quick_watch_query_is_generated() -> None:
    queries = build_watch_queries(["personalized_nutrition"], since_days=30, mode="quick")
    query_text = "\n".join(str(item["query"]) for item in queries)

    assert queries
    assert "precision nutrition type 2 diabetes" in query_text
    assert "tailored dietary advice cardiometabolic risk" in query_text
    assert "obesity" in query_text or "cardiometabolic" in query_text
