from __future__ import annotations

from pathlib import Path

from nutev.settings import load_json


def _load_project_scoring_rules() -> dict:
    repo_root = Path(__file__).resolve().parents[1]
    return load_json(repo_root / "config" / "scoring_rules.json")


def test_personalized_nutrition_supplement_terms_are_loaded() -> None:
    rules = _load_project_scoring_rules()
    keyword_points = rules["keyword_points"]

    expected_points = {
        "personalized nutrition obesity": 4,
        "personalised nutrition obesity": 4,
        "precision nutrition type 2 diabetes": 4,
        "tailored dietary advice cardiometabolic risk": 4,
        "individualized dietary intervention type 2 diabetes": 4,
        "individualised dietary intervention type 2 diabetes": 4,
        "personalized meal planning obesity": 3,
        "personalised meal planning type 2 diabetes": 3,
    }

    assert {term: keyword_points[term] for term in expected_points} == expected_points


def test_personalized_nutrition_supplement_adds_workstream_bonuses() -> None:
    rules = _load_project_scoring_rules()

    assert rules["workstream_bonus"]["busca2a"][
        "precision nutrition cardiometabolic risk"
    ] == 4
    assert rules["workstream_bonus"]["busca2b"][
        "tailored dietary intervention obesity"
    ] == 4
    assert rules["workstream_bonus"]["busca2b"][
        "personalized meal planning type 2 diabetes"
    ] == 3
