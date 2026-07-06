from pathlib import Path

from nutev.settings import load_json


def test_personalized_adherence_supplement_is_loaded() -> None:
    taxonomy = load_json(Path(__file__).resolve().parents[1] / "config" / "keyword_taxonomy.json")

    personalized_terms = taxonomy["global"]["implementation_behavior"]["personalized_adherence"]
    assert "personalized nutrition intervention" in personalized_terms
    assert "shared decision making" in personalized_terms
    assert "digital nutrition intervention" in personalized_terms

    busca2b = taxonomy["workstreams"]["busca2b"]
    assert "personalized_adherence" in busca2b["priority_outcomes"]
    assert "precision nutrition intervention" in busca2b["web_query_hints"]

    framework = taxonomy["workstreams"]["artigo3_framework"]
    assert "personalized_adherence" in framework["priority_outcomes"]
    assert "digital nutrition adherence framework" in framework["web_query_hints"]


def test_social_prescribing_supplement_is_loaded_for_food_referrals() -> None:
    taxonomy = load_json(Path(__file__).resolve().parents[1] / "config" / "keyword_taxonomy.json")

    social_terms = taxonomy["global"]["implementation_behavior"]["social_prescribing_food_referrals"]
    assert "social prescribing food referral" in social_terms
    assert "food as medicine referral" in social_terms
    assert "closed-loop food referral" in social_terms

    busca1 = taxonomy["workstreams"]["busca1"]
    assert "nutrition security referral" in busca1["focus_terms"]
    assert "food as medicine referral implementation report" in busca1["web_query_hints"]

    busca2b = taxonomy["workstreams"]["busca2b"]
    assert "social prescribing nutrition referral" in busca2b["focus_terms"]
    assert "closed-loop food referral implementation trial" in busca2b["web_query_hints"]
    assert "program evaluation" in busca2b["document_terms"]
