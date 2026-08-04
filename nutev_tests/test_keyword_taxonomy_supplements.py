from pathlib import Path

from nutev.querypacks.builders import build_querypack
from nutev.settings import load_json


def _taxonomy() -> dict:
    return load_json(Path(__file__).resolve().parents[1] / "config" / "keyword_taxonomy.json")


def test_personalized_adherence_supplement_is_loaded() -> None:
    taxonomy = _taxonomy()

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


def _rendered_querypack() -> str:
    querypack = build_querypack(_taxonomy(), ["busca2a", "busca2b", "a3"])
    return "\n".join(
        query.lower()
        for queries in querypack.values()
        for query in queries
    )


def test_personalized_metabolic_supplement_expands_precision_nutrition_terms() -> None:
    rendered = _rendered_querypack()

    assert "personalized nutrition" in rendered
    assert "precision nutrition" in rendered
    assert "tailored dietary intervention" in rendered
    assert "diet personalization" in rendered


def test_personalized_metabolic_supplement_expands_remission_and_maintenance_terms() -> None:
    rendered = _rendered_querypack()

    assert "type 2 diabetes remission" in rendered
    assert "nutrition care for diabetes remission" in rendered
    assert "weight loss maintenance" in rendered
    assert "weight regain prevention" in rendered


def test_personalized_metabolic_supplement_expands_anti_obesity_medication_terms() -> None:
    rendered = _rendered_querypack()

    assert "anti-obesity medication nutrition" in rendered
    assert "glp-1 nutrition" in rendered
    assert "glp-1 dietary adherence" in rendered
    assert "incretin therapy nutrition intervention" in rendered
