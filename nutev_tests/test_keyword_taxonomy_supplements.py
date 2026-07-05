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


def test_glp1_nutrition_care_supplement_is_loaded() -> None:
    taxonomy = load_json(Path(__file__).resolve().parents[1] / "config" / "keyword_taxonomy.json")

    nutrition_domains = taxonomy["global"]["nutrition_domains"]
    glp1_terms = nutrition_domains["anti_obesity_pharmacotherapy_nutrition"]
    protein_terms = nutrition_domains["lean_mass_protein_preservation"]

    assert "glp-1 receptor agonist nutrition" in glp1_terms
    assert "semaglutide nutrition counseling" in glp1_terms
    assert "lean mass preservation" in protein_terms
    assert "protein adequacy" in protein_terms

    busca2a_hints = taxonomy["workstreams"]["busca2a"]["web_query_hints"]
    assert "glp-1 nutrition guidance" in busca2a_hints
    assert "protein adequacy obesity treatment" in busca2a_hints

    busca2b_hints = taxonomy["workstreams"]["busca2b"]["web_query_hints"]
    assert "glp-1 nutrition intervention" in busca2b_hints
    assert "protein adequacy weight loss maintenance" in busca2b_hints
