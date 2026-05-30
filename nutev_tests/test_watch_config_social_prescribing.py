from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES


def test_lifestyle_watch_category_covers_social_prescribing_terms() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["lifestyle_medicine"]}

    assert "social prescribing" in terms
    assert "community referral" in terms
    assert "food navigator" in terms
    assert "community health worker" in terms


def test_implementation_watch_category_covers_navigation_and_referral_terms() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["implementation_behavior"]}

    assert "social prescription" in terms
    assert "link worker" in terms
    assert "patient navigation" in terms
    assert "nutrition navigator" in terms
