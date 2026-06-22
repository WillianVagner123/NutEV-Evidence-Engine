from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES


def test_personalized_nutrition_watch_queries_cover_intervention_variants() -> None:
    rendered = " ".join(
        term
        for bucket in WATCH_CATEGORIES["personalized_nutrition"]
        for term in bucket
    ).lower()

    assert "personalized nutrition intervention" in rendered
    assert "personalised nutrition intervention" in rendered
    assert "precision nutrition intervention" in rendered
    assert "personalized dietary intervention obesity" in rendered
    assert "personalised dietary intervention obesity" in rendered
    assert "personalized dietary intervention cardiometabolic risk" in rendered
    assert "personalised dietary intervention cardiometabolic risk" in rendered
