from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES


def test_obesity_watch_category_covers_weight_maintenance_and_remission_terms() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["obesity_cardiometabolic"]}

    assert "type 2 diabetes remission" in terms
    assert "remission of type 2 diabetes" in terms
    assert "diabetes prevention program" in terms
    assert "long-term weight management" in terms
    assert "weight maintenance" in terms
    assert "weight loss maintenance" in terms
    assert "weight regain" in terms


def test_implementation_watch_category_covers_adherence_maintenance_terms() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["implementation_behavior"]}

    assert "long-term adherence" in terms
    assert "dietary maintenance" in terms
    assert "weight maintenance" in terms
    assert "weight loss maintenance" in terms
    assert "weight regain" in terms
    assert "relapse prevention" in terms


def test_diet_pattern_watch_category_covers_quality_pattern_terms() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["diet_patterns"]}

    assert "healthy eating pattern" in terms
    assert "healthy dietary pattern" in terms
    assert "diet quality" in terms
