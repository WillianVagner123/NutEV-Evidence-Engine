from __future__ import annotations

from pathlib import Path

from nutev.settings import load_json


def test_food_access_program_supplement_loads_into_taxonomy() -> None:
    config_root = Path(__file__).resolve().parents[1] / "config"
    loaded = load_json(config_root / "keyword_taxonomy.json")

    food_access_terms = loaded["global"]["implementation_behavior"][
        "food_as_medicine_access"
    ]
    busca2b_hints = loaded["workstreams"]["busca2b"]["web_query_hints"]

    assert "food is medicine program" in food_access_terms
    assert "fresh food pharmacy program" in food_access_terms
    assert "grocery prescription cardiometabolic trial" in busca2b_hints
