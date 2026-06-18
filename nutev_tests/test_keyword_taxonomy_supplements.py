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


def test_adherence_score_supplement_is_loaded() -> None:
    taxonomy = load_json(Path(__file__).resolve().parents[1] / "config" / "keyword_taxonomy.json")

    adherence_terms = taxonomy["global"]["implementation_behavior"][
        "dietary_adherence_measurement"
    ]
    busca2b_focus_terms = taxonomy["workstreams"]["busca2b"]["focus_terms"]
    artigo3_focus_terms = taxonomy["workstreams"]["artigo3_framework"]["focus_terms"]

    assert "mediterranean diet adherence screener" in adherence_terms
    assert "dash adherence score" in taxonomy["outcomes"]["diet_quality_adherence"]
    assert "plant-based diet index" in busca2b_focus_terms
    assert "dietary adherence instrument" in artigo3_focus_terms
