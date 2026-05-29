from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES


def test_watch_categories_include_cardiometabolic_remission_terms() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["cardiometabolic_remission"]}

    assert "type 2 diabetes remission" in terms
    assert "glycemic remission" in terms
    assert "glycaemic remission" in terms
    assert "prediabetes remission" in terms
    assert "weight loss maintenance" in terms
    assert "total diet replacement" in terms
    assert "medical nutrition therapy" in terms
    assert "dietary adherence" in terms
