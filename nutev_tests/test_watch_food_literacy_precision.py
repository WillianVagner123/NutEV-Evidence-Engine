from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES
from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item


def test_food_literacy_queries_add_labeling_and_security_context() -> None:
    queries = build_watch_queries(
        ["food_literacy_culinary_commensality"],
        since_days=30,
        mode="quick",
    )

    first_query = str(queries[0]["query"])
    assert '"nutrition security"' in first_query
    assert '"nutrition label"' in first_query
    assert '"label reading"' in first_query
    assert '"front-of-pack"' in first_query
    assert '"front-of-pack labeling"' in first_query
    assert '"front-of-pack labelling"' in first_query


def test_watch_categories_include_food_security_and_equity_context() -> None:
    implementation_terms = set(WATCH_CATEGORIES["implementation_behavior"])
    food_literacy_terms = set(WATCH_CATEGORIES["food_literacy_culinary_commensality"])

    assert "food insecurity" in implementation_terms
    assert "nutrition security" in implementation_terms
    assert "health equity" in implementation_terms
    assert "healthy food availability" in food_literacy_terms
    assert "food affordability" in food_literacy_terms
    assert "social determinants of health" in food_literacy_terms


def test_labeling_and_security_signals_improve_priority() -> None:
    enriched = score_watch_item(
        {
            "title": "Nutrition security and front-of-pack labeling to improve food literacy in obesity care",
        }
    )
    generic = score_watch_item({"title": "Food literacy in obesity care"})

    assert enriched > generic


def test_food_security_and_equity_signals_improve_priority() -> None:
    enriched = score_watch_item(
        {
            "title": "Food insecurity and health equity implementation strategy for obesity care",
            "abstract": "Healthy food availability and affordability improved dietary adherence.",
            "category": "implementation_behavior",
        }
    )
    generic = score_watch_item(
        {
            "title": "Implementation strategy for obesity care",
            "abstract": "Dietary adherence improved.",
            "category": "implementation_behavior",
        }
    )

    assert enriched > generic
