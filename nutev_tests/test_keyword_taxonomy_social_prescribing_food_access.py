from __future__ import annotations

from pathlib import Path

from nutev.settings import load_json


def test_social_prescribing_food_access_supplement_is_loaded() -> None:
    taxonomy = load_json(Path(__file__).resolve().parents[1] / "config" / "keyword_taxonomy.json")

    social_prescribing_terms = taxonomy["global"]["implementation_behavior"][
        "social_prescribing_food_access"
    ]
    assert "food social prescribing" in social_prescribing_terms
    assert "nutrition social prescribing" in social_prescribing_terms
    assert "community food referral" in social_prescribing_terms
    assert "food access referral pathway" in social_prescribing_terms

    busca1 = taxonomy["workstreams"]["busca1"]
    assert "food is medicine" in busca1["focus_terms"]
    assert "social prescribing food insecurity" in busca1["focus_terms"]
    assert "community nutrition referral pathway" in busca1["web_query_hints"]

    busca2b = taxonomy["workstreams"]["busca2b"]
    assert "dietitian-led intervention" in busca2b["focus_terms"]
    assert "social prescribing produce prescription" in busca2b["focus_terms"]
    assert "food social prescribing trial" in busca2b["web_query_hints"]

    framework = taxonomy["workstreams"]["artigo3_framework"]
    assert "food literacy questionnaire" in framework["focus_terms"]
    assert "food social prescribing framework" in framework["focus_terms"]
    assert "referral pathway" in framework["document_terms"]
