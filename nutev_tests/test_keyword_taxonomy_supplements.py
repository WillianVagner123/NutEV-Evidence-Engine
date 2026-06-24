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


def test_personalized_precision_nutrition_supplement_reaches_cardiometabolic_querypacks() -> None:
    taxonomy = load_json(Path(__file__).resolve().parents[1] / "config" / "keyword_taxonomy.json")
    querypack = build_querypack(taxonomy, ["busca2a", "busca2b"])
    rendered = "\n".join(
        query for queries in querypack.values() for query in queries
    ).lower()

    assert "phenotype-guided nutrition" in rendered
    assert "algorithm-guided dietary advice" in rendered
    assert "risk-stratified dietary intervention" in rendered
    assert "type 2 diabetes remission" in rendered
    assert "weight regain prevention" in rendered
    assert "tailored dietary intervention cardiometabolic risk" in rendered
