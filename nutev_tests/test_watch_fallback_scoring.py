from __future__ import annotations

from nutev.global_watch.watch_scoring import score_watch_item


def test_synthetic_fallback_watch_item_is_not_high_priority() -> None:
    item = {
        "title": "global watch fallback item",
        "url": "https://fallback.local",
        "source_provider": "watch_seed",
        "category": "guidelines_consensus",
        "relevance_score": 50,
        "is_new": True,
        "fallback_used": True,
    }

    assert score_watch_item(item) <= 5


def test_real_guideline_can_still_score_high_priority() -> None:
    item = {
        "title": "Clinical practice guideline for obesity nutrition care",
        "source_provider": "pubmed",
        "category": "guidelines_consensus",
        "relevance_score": 50,
        "is_new": True,
    }

    assert score_watch_item(item) >= 80


def test_diet_engagement_and_retention_signal_scores_high_priority() -> None:
    item = {
        "title": "Dietary intervention engagement and retention for obesity care",
        "abstract": "A pragmatic nutrition counseling program for cardiometabolic risk tracks intervention dose and session attendance.",
        "source_provider": "pubmed",
        "category": "implementation_behavior",
        "relevance_score": 20,
        "is_new": True,
    }

    assert score_watch_item(item) >= 80
