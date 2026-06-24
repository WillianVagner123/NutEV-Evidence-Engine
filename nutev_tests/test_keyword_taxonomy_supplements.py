from pathlib import Path

from nutev.querypacks.builders import build_queries
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


def test_nutrition_prescription_supplement_reaches_querypack() -> None:
    taxonomy = load_json(Path(__file__).resolve().parents[1] / "config" / "keyword_taxonomy.json")

    nutrition_terms = taxonomy["global"]["nutrition_domains"][
        "nutrition_prescription_protocols"
    ]
    assert "nutrition prescription" in nutrition_terms
    assert "dietary care pathway" in nutrition_terms

    busca2a_queries = "\n".join(build_queries(taxonomy, "busca2a")).lower()
    busca2b_queries = "\n".join(build_queries(taxonomy, "busca2b")).lower()

    assert "nutrition prescription" in busca2a_queries
    assert "dietary care pathway" in busca2a_queries
    assert "nutrition prescription adherence" in busca2b_queries
    assert "dietary prescription implementation" in busca2b_queries
