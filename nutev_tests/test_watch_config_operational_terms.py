from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES


def test_lifestyle_watch_category_covers_primary_care_nutrition_referrals() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["lifestyle_medicine"]}

    assert "primary care nutrition" in terms
    assert "nutrition-sensitive primary care" in terms
    assert "nutrition referral" in terms
    assert "dietitian referral" in terms
    assert "social prescribing" in terms


def test_implementation_watch_category_covers_referral_and_social_prescribing_terms() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["implementation_behavior"]}

    assert "social prescribing" in terms
    assert "nutrition referral" in terms
    assert "dietitian referral" in terms
    assert "food referral" in terms
    assert "community referral" in terms
    assert "nutrition-sensitive primary care" in terms
