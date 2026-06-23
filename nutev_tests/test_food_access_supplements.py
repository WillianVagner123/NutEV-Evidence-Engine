from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_config(name: str) -> dict:
    return json.loads((REPO_ROOT / "config" / name).read_text(encoding="utf-8"))


def test_food_access_query_supplement_has_effective_query_inputs() -> None:
    data = _load_config("keyword_taxonomy_supplement_food_access_20260623.json")

    nutrition_terms = data["global"]["nutrition_domains"]["culinary_labeling"]
    behavior_terms = data["global"]["implementation_behavior"]["food_as_medicine_access"]
    busca1_hints = data["workstreams"]["busca1"]["web_query_hints"]
    busca2b_hints = data["workstreams"]["busca2b"]["web_query_hints"]

    assert "grocery prescription" in nutrition_terms
    assert "healthy food box" in nutrition_terms
    assert "health-related social needs" in behavior_terms
    assert "food is medicine program evaluation" in behavior_terms
    assert "food is medicine program evaluation" in busca1_hints
    assert "grocery prescription intervention diabetes" in busca2b_hints


def test_food_access_scoring_supplement_prioritizes_program_terms() -> None:
    data = _load_config("scoring_rules_supplement_food_access_20260623.json")

    keyword_points = data["keyword_points"]
    busca1_bonus = data["workstream_bonus"]["busca1"]
    busca2b_bonus = data["workstream_bonus"]["busca2b"]

    assert keyword_points["food pharmacy intervention"] >= 4
    assert keyword_points["health-related social needs"] >= 3
    assert busca1_bonus["grocery prescription"] >= 5
    assert busca2b_bonus["medically tailored meals implementation"] >= 5
