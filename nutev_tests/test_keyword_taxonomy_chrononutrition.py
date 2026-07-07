from __future__ import annotations

from pathlib import Path

from nutev.querypacks.builders import build_queries
from nutev.settings import load_json


CONFIG_ROOT = Path(__file__).resolve().parents[1] / "config"


def test_chrononutrition_supplement_is_merged_into_taxonomy() -> None:
    taxonomy = load_json(CONFIG_ROOT / "keyword_taxonomy.json")

    diet_terms = taxonomy["global"]["diet_patterns"]
    behavior_terms = taxonomy["global"]["implementation_behavior"]["behavioral"]
    busca2b_hints = taxonomy["workstreams"]["busca2b"]["web_query_hints"]

    assert "chrononutrition_metabolic_timing" in diet_terms
    assert "early time-restricted eating" in diet_terms["chrononutrition_metabolic_timing"]
    assert "time-restricted eating adherence" in behavior_terms
    assert "chrononutrition systematic review" in busca2b_hints


def test_busca2b_queries_include_chrononutrition_metabolic_timing_terms() -> None:
    taxonomy = load_json(CONFIG_ROOT / "keyword_taxonomy.json")
    queries = build_queries(taxonomy, "busca2b")
    rendered = "\n".join(queries).lower()

    assert "chrononutrition" in rendered
    assert "meal timing" in rendered
    assert "early time-restricted eating" in rendered
    assert "time-restricted eating adherence" in rendered
    assert "late eating cardiometabolic risk" in rendered
