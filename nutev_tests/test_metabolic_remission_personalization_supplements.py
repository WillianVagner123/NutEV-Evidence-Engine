from __future__ import annotations

from nutev.settings import default_config_root, load_json


def test_metabolic_remission_supplement_reaches_clinical_workstreams() -> None:
    taxonomy = load_json(default_config_root() / "keyword_taxonomy.json")

    busca2a = taxonomy["workstreams"]["busca2a"]
    busca2b = taxonomy["workstreams"]["busca2b"]

    assert "nutrition care for diabetes remission" in busca2a["focus_terms"]
    assert "type 2 diabetes remission" in busca2b["focus_terms"]
    assert "weight regain prevention" in busca2b["focus_terms"]
    assert "precision nutrition type 2 diabetes trial" in busca2b["web_query_hints"]


def test_personalized_nutrition_supplement_reaches_framework_workstreams() -> None:
    taxonomy = load_json(default_config_root() / "keyword_taxonomy.json")

    artigo3 = taxonomy["workstreams"]["artigo3_framework"]

    assert "personalized nutrition" in artigo3["focus_terms"]
    assert "personalised nutrition" in artigo3["focus_terms"]
    assert "precision nutrition framework" in artigo3["document_terms"]


def test_metabolic_remission_scoring_terms_are_loaded() -> None:
    scoring = load_json(default_config_root() / "scoring_rules.json")

    assert scoring["keyword_points"]["nutrition care for diabetes remission"] == 5
    assert scoring["workstream_bonus"]["busca2b"]["weight regain prevention"] == 5
    assert scoring["workstream_bonus"]["a3"]["precision nutrition"] == 4
