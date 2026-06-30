from pathlib import Path

from nutev.querypacks.builders import build_structured_components
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


def test_food_access_supplement_expands_busca1_terms() -> None:
    taxonomy = load_json(Path(__file__).resolve().parents[1] / "config" / "keyword_taxonomy.json")
    _, components = build_structured_components(taxonomy, "busca1")
    rendered = " ".join(
        components["nutrition_terms"]
        + components["behavior_terms"]
        + components["web_hints"]
    ).lower()

    assert "healthy food box" in rendered
    assert "grocery prescription" in rendered
    assert "food pharmacy program" in rendered
    assert "food access referral" in rendered


def test_food_access_supplement_expands_busca2b_terms() -> None:
    taxonomy = load_json(Path(__file__).resolve().parents[1] / "config" / "keyword_taxonomy.json")
    _, components = build_structured_components(taxonomy, "busca2b")
    rendered = " ".join(components["web_hints"]).lower()

    assert "healthy food box trial" in rendered
    assert "grocery prescription trial" in rendered
    assert "medically tailored food referral" in rendered
