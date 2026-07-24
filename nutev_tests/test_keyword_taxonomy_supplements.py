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


def test_lifestyle_medicine_nutrition_supplement_is_loaded() -> None:
    taxonomy = load_json(Path(__file__).resolve().parents[1] / "config" / "keyword_taxonomy.json")

    nutrition_terms = taxonomy["global"]["lifestyle_medicine_pillars"]["nutrition"]
    implementation_terms = taxonomy["global"]["implementation_behavior"]["lifestyle_medicine_delivery"]
    assert "nutrition-focused lifestyle medicine" in nutrition_terms
    assert "lifestyle medicine dietary intervention" in nutrition_terms
    assert "comprehensive lifestyle intervention" in implementation_terms

    busca1 = taxonomy["workstreams"]["busca1"]
    assert "lifestyle medicine nutrition guideline" in busca1["web_query_hints"]
    assert "nutrition-focused lifestyle medicine" in busca1["focus_terms"]

    busca2b = taxonomy["workstreams"]["busca2b"]
    assert "lifestyle medicine nutrition intervention trial" in busca2b["web_query_hints"]
    assert "intensive lifestyle intervention with nutrition" in busca2b["focus_terms"]

    framework = taxonomy["workstreams"]["artigo3_framework"]
    assert "whole person lifestyle medicine framework" in framework["web_query_hints"]
    assert "lifestyle medicine coaching" in framework["focus_terms"]
