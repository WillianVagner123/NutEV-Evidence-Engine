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


def test_precision_nutrition_supplement_adds_clinical_food_assistance_terms() -> None:
    taxonomy = load_json(Path(__file__).resolve().parents[1] / "config" / "keyword_taxonomy.json")

    clinical_food_assistance = taxonomy["global"]["implementation_behavior"][
        "clinical_food_assistance"
    ]
    for term in [
        "grocery prescription intervention",
        "nutrition pharmacy program evaluation",
        "food farmacy program evaluation",
        "medically tailored grocery intervention",
        "produce prescription implementation study",
    ]:
        assert term in clinical_food_assistance

    busca2b = taxonomy["workstreams"]["busca2b"]
    for term in [
        "food prescription intervention",
        "medically tailored meal intervention",
        "medically tailored grocery program evaluation",
        "produce prescription implementation study",
    ]:
        assert term in busca2b["focus_terms"]
        assert term in busca2b["web_query_hints"]

    for term in [
        "food prescription intervention trial",
        "grocery prescription program evaluation",
        "healthy food incentive program evaluation",
    ]:
        assert term in busca2b["document_terms"]
