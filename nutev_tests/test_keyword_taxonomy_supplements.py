from pathlib import Path

from nutev.querypacks.builders import build_structured_components
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


def test_habit_relapse_maintenance_supplement_is_loaded() -> None:
    taxonomy = load_json(Path(__file__).resolve().parents[1] / "config" / "keyword_taxonomy.json")

    habit_terms = taxonomy["global"]["implementation_behavior"]["habit_relapse_maintenance"]
    assert "dietary habit formation" in habit_terms
    assert "lapse management" in habit_terms
    assert "dietary relapse prevention" in habit_terms

    _, busca2b_components = build_structured_components(taxonomy, "busca2b")
    assert "dietary lapse" in busca2b_components["focus_terms"]
    assert "habit formation intervention" in busca2b_components["web_hints"]
    assert "relapse prevention intervention" in busca2b_components["doc_type_terms"]

    _, framework_components = build_structured_components(taxonomy, "artigo3_framework")
    assert "habit strength" in framework_components["focus_terms"]
    assert "self-regulation of eating questionnaire" in framework_components["web_hints"]
