from __future__ import annotations

from pathlib import Path

from nutev.settings import load_json


def test_cardiometabolic_obesity_keyword_supplement_is_loaded() -> None:
    taxonomy = load_json(Path("config/keyword_taxonomy.json"))

    obesity_terms = taxonomy["clinical"]["obesity"]
    busca2a_terms = taxonomy["workstreams"]["busca2a"]["condition_terms"]
    busca2b_hints = taxonomy["workstreams"]["busca2b"]["web_query_hints"]

    assert "obesity staging" in obesity_terms
    assert "adiposity-related complications" in obesity_terms
    assert "cardiovascular-kidney-metabolic syndrome" in busca2a_terms
    assert "weight regain prevention trial" in busca2b_hints


def test_cardiometabolic_obesity_scoring_supplement_is_loaded() -> None:
    scoring = load_json(Path("config/scoring_rules.json"))

    assert scoring["keyword_points"]["cardiometabolic obesity"] == 5
    assert scoring["keyword_points"]["ckm syndrome"] == 4
    assert scoring["workstream_bonus"]["busca2a"]["obesity complications"] == 5
    assert scoring["workstream_bonus"]["busca2b"]["weight regain prevention"] == 5
