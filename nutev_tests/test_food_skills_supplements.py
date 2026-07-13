from __future__ import annotations

from pathlib import Path

from nutev.querypacks.builders import build_structured_components
from nutev.settings import load_json


CONFIG_ROOT = Path(__file__).resolve().parents[1] / "config"


def test_food_skills_taxonomy_supplement_is_loaded_into_query_components() -> None:
    taxonomy = load_json(CONFIG_ROOT / "keyword_taxonomy.json")

    _, busca2b_components = build_structured_components(taxonomy, "busca2b")
    _, article3_components = build_structured_components(taxonomy, "a3")

    assert "food skills intervention" in busca2b_components["behavior_terms"]
    assert "cooking self-efficacy" in busca2b_components["nutrition_terms"]
    assert "nutrition label use" in article3_components["nutrition_terms"]


def test_food_skills_scoring_supplement_is_loaded() -> None:
    scoring = load_json(CONFIG_ROOT / "scoring_rules.json")

    assert scoring["keyword_points"]["cooking self-efficacy"] == 4
    assert scoring["workstream_bonus"]["busca2b"]["food skills intervention"] == 5
    assert scoring["workstream_bonus"]["artigo3_framework"]["food skills scale"] == 5
