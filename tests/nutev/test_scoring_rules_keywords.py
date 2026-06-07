from __future__ import annotations

import json
from pathlib import Path


def _load_scoring_rules() -> dict:
    repo_root = Path(__file__).resolve().parents[2]
    config_path = repo_root / "config" / "scoring_rules.json"
    return json.loads(config_path.read_text(encoding="utf-8"))


def test_scoring_rules_cover_food_environment_and_food_as_medicine_terms() -> None:
    keyword_points = _load_scoring_rules()["keyword_points"]

    expected_points = {
        "culinary nutrition": 3,
        "retail food environment": 3,
        "healthy food procurement": 3,
        "front-of-pack labeling": 3,
        "front-of-pack labelling": 3,
        "menu labeling": 2,
        "menu labelling": 2,
        "produce rx": 4,
        "fruit and vegetable prescription": 4,
        "healthy food prescription": 4,
        "food prescription program": 4,
        "scale-out": 2,
        "scale out": 2,
    }

    assert {term: keyword_points[term] for term in expected_points} == expected_points
