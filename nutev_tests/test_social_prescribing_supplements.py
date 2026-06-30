from pathlib import Path

from nutev.settings import load_json


def test_social_prescribing_terms_are_loaded_from_keyword_taxonomy_supplement() -> None:
    taxonomy = load_json(Path("config") / "keyword_taxonomy.json")

    terms = taxonomy["global"]["implementation_behavior"]["social_prescribing_nutrition"]
    assert "social prescribing nutrition" in terms
    assert "food referral pathway" in terms
    assert "closed-loop referral nutrition" in terms
    assert "primary care produce prescription" in terms

    busca2b_terms = taxonomy["workstreams"]["busca2b"]["focus_terms"]
    assert "social prescribing cardiometabolic" in busca2b_terms
    assert "patient navigation nutrition" in busca2b_terms


def test_social_prescribing_terms_are_loaded_from_scoring_supplement() -> None:
    scoring = load_json(Path("config") / "scoring_rules.json")
    keyword_points = scoring["keyword_points"]

    assert keyword_points["social prescribing nutrition"] == 4
    assert keyword_points["social prescribing cardiometabolic"] == 4
    assert keyword_points["primary care produce prescription"] == 4
    assert keyword_points["patient navigation nutrition"] == 3
