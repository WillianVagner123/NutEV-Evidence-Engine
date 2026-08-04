from __future__ import annotations

from pathlib import Path

from nutev.settings import load_json


def test_cardiorenal_scoring_supplement_covers_ckm_variants() -> None:
    supplement = load_json(Path("config/scoring_rules_supplement_cardiorenal.json"))
    keyword_points = supplement["keyword_points"]
    busca2a_bonus = supplement["workstream_bonus"]["busca2a"]
    busca2b_bonus = supplement["workstream_bonus"]["busca2b"]

    expected_terms = {
        "cardiovascular-kidney-metabolic syndrome": 4,
        "cardiovascular kidney metabolic syndrome": 4,
        "cardio-kidney-metabolic nutrition": 3,
        "cardio kidney metabolic nutrition": 3,
        "cardiorenal metabolic risk": 3,
        "ckm syndrome": 4,
        "ckm nutrition": 3,
    }

    assert {term: keyword_points[term] for term in expected_terms} == expected_terms
    assert all(busca2a_bonus[term] == 5 for term in expected_terms)
    assert all(busca2b_bonus[term] == 5 for term in expected_terms)
