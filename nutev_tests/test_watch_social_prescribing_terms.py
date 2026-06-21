from nutev.global_watch.watch_config import WATCH_CATEGORIES


def test_implementation_terms_include_nutrition_anchored_social_prescribing_referrals() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["implementation_behavior"]}

    expected_terms = {
        "nutrition referral",
        "dietitian referral",
        "dietitian referral pathway",
        "healthy food referral",
        "food resource referral",
        "fresh food prescription",
        "fresh produce prescription",
        "community-supported agriculture prescription",
        "community supported agriculture prescription",
        "csa prescription",
    }

    assert expected_terms <= terms
