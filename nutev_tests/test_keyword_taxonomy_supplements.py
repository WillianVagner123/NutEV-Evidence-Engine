from pathlib import Path

from nutev.settings import load_json


def _load_taxonomy() -> dict:
    return load_json(Path(__file__).resolve().parents[1] / "config" / "keyword_taxonomy.json")


def test_personalized_adherence_supplement_is_loaded() -> None:
    taxonomy = _load_taxonomy()

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


def test_adherence_implementation_supplement_is_loaded() -> None:
    taxonomy = _load_taxonomy()

    adherence_terms = taxonomy["global"]["implementation_behavior"]["adherence"]
    behavioral_terms = taxonomy["global"]["implementation_behavior"]["behavioral"]
    care_delivery_terms = taxonomy["global"]["implementation_behavior"]["care_delivery"]
    diet_adherence_terms = taxonomy["global"]["diet_patterns"]["adherence_indices"]

    assert "dietary adherence counseling" in adherence_terms
    assert "dietary relapse prevention" in behavioral_terms
    assert "nutrition coaching" in care_delivery_terms
    assert "Mediterranean diet adherence score" in diet_adherence_terms
