from __future__ import annotations

from nutev.querypacks.builders import build_querypack
from nutev.settings import default_config_root, load_json


def test_personalized_nutrition_supplement_reaches_busca2_querypacks() -> None:
    taxonomy = load_json(default_config_root() / "keyword_taxonomy.json")
    querypack = build_querypack(taxonomy, ["busca2a", "busca2b"])

    busca2a_queries = "\n".join(querypack["busca2a"]).lower()
    busca2b_queries = "\n".join(querypack["busca2b"]).lower()

    assert "personalized nutrition counseling" in busca2a_queries
    assert "precision nutrition implementation" in busca2b_queries
    assert "tailored dietary adherence" in busca2b_queries
    assert "anti-obesity medication nutrition intervention" in busca2b_queries
    assert "glp-1 dietary adherence" in busca2b_queries


def test_personalized_nutrition_scoring_supplement_is_merged() -> None:
    scoring = load_json(default_config_root() / "scoring_rules.json")

    keyword_points = scoring["keyword_points"]
    assert keyword_points["precision nutrition implementation"] == 3
    assert keyword_points["tailored dietary adherence"] == 3
    assert keyword_points["glp-1 dietary adherence"] == 3
