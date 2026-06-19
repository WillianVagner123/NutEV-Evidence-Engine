from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES
from nutev.global_watch.watch_query_builder import build_watch_queries


def _rendered_category_terms(category: str) -> str:
    return "\n".join(WATCH_CATEGORIES[category]).lower()


def test_watch_config_preserves_a3_food_competence_and_commensality_instruments() -> None:
    rendered = _rendered_category_terms("frameworks_instruments")

    expected_terms = [
        "food competence scale",
        "food competence questionnaire",
        "eating competence scale",
        "commensality scale",
        "shared meals scale",
        "family meals scale",
        "diet personalization scale",
        "cooking self-efficacy scale",
        "meal planning questionnaire",
        "food label literacy scale",
    ]

    for term in expected_terms:
        assert term in rendered


def test_quick_watch_framework_queries_keep_adherence_and_culinary_instrument_seeds() -> None:
    queries = build_watch_queries(["frameworks_instruments"], since_days=7, mode="quick")
    rendered = "\n".join(str(row["query"]).lower() for row in queries)

    assert "adherence scale" in rendered
    assert "food literacy instrument" in rendered
    assert "culinary skills instrument" in rendered
    assert "psychometric validation" in rendered
    assert "questionnaire validation" in rendered
