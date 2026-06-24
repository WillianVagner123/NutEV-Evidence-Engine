from pathlib import Path

from nutev.querypacks.builders import build_structured_components
from nutev.settings import load_json


CONFIG_ROOT = Path(__file__).resolve().parents[1] / "config"


def test_personalized_adherence_supplement_is_loaded() -> None:
    taxonomy = load_json(CONFIG_ROOT / "keyword_taxonomy.json")

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


def test_metabolic_remission_supplement_extends_busca2_components() -> None:
    taxonomy = load_json(CONFIG_ROOT / "keyword_taxonomy.json")

    _, busca2a = build_structured_components(taxonomy, "busca2a")
    _, busca2b = build_structured_components(taxonomy, "busca2b")

    assert "diabetes remission guideline" in busca2a["web_hints"]
    assert "weight regain prevention guideline" in busca2a["web_hints"]
    assert "type 2 diabetes remission intervention" in busca2b["web_hints"]
    assert "dietitian-led remission intervention" in busca2b["web_hints"]
    assert "diabetes remission diet" in busca2b["diet_terms"]
    assert "weight loss maintenance diet" in busca2b["diet_terms"]
