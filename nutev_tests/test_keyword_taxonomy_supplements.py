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


def test_metabolic_maintenance_supplement_reaches_busca2b_queries() -> None:
    taxonomy = load_json(Path(__file__).resolve().parents[1] / "config" / "keyword_taxonomy.json")

    assert "diabetes remission" in taxonomy["clinical"]["diabetes"]
    assert "weight regain prevention" in taxonomy["clinical"]["obesity"]

    busca2b_queries = build_querypack(taxonomy, ["busca2b"])["busca2b"]
    rendered_queries = "\n".join(busca2b_queries).lower()

    assert "diabetes remission" in rendered_queries
    assert "weight regain prevention" in rendered_queries
    assert "personalized nutrition" in rendered_queries
