from pathlib import Path

from nutev.querypacks.builders import build_querypack
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


def test_ckm_supplement_reaches_clinical_querypacks() -> None:
    taxonomy = load_json(Path(__file__).resolve().parents[1] / "config" / "keyword_taxonomy.json")

    querypack = build_querypack(taxonomy, ["busca2a", "busca2b"])
    busca2a_queries = "\n".join(querypack["busca2a"]).lower()
    busca2b_queries = "\n".join(querypack["busca2b"]).lower()

    assert "cardiovascular-kidney-metabolic" in busca2a_queries
    assert "ckm syndrome" in busca2a_queries
    assert "cardiovascular-kidney-metabolic" in busca2b_queries
    assert "ckm syndrome" in busca2b_queries
