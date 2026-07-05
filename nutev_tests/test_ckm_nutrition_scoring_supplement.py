from pathlib import Path

from nutev.settings import load_json


def test_ckm_nutrition_scoring_supplement_is_merged() -> None:
    scoring = load_json(Path("config/scoring_rules.json"))

    assert scoring["keyword_points"]["ckm syndrome nutrition therapy"] == 5
    assert scoring["keyword_points"]["cardiorenal metabolic dietary intervention"] == 5
    assert scoring["workstream_bonus"]["busca2a"]["ckm scientific statement"] == 6
    assert scoring["workstream_bonus"]["busca2b"]["ckm syndrome systematic review"] == 6
