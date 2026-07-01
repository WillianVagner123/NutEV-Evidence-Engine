from pathlib import Path

from nutev.querypacks.builders import build_queries
from nutev.settings import load_json


ROOT = Path(__file__).resolve().parents[1]


def test_personalized_adherence_supplement_is_loaded() -> None:
    taxonomy = load_json(ROOT / "config" / "keyword_taxonomy.json")

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


def test_behavior_maintenance_supplement_feeds_structured_queries() -> None:
    taxonomy = load_json(ROOT / "config" / "keyword_taxonomy.json")

    behavior_terms = taxonomy["global"]["implementation_behavior"][
        "maintenance_self_management"
    ]
    assert "dietary self-monitoring" in behavior_terms
    assert "weight regain prevention" in behavior_terms

    busca2b_queries = "\n".join(build_queries(taxonomy, "busca2b")).lower()
    a3_queries = "\n".join(build_queries(taxonomy, "artigo3_framework")).lower()

    assert "dietary self-monitoring" in busca2b_queries
    assert "weight regain prevention" in busca2b_queries
    assert "dietary self-monitoring" in a3_queries
