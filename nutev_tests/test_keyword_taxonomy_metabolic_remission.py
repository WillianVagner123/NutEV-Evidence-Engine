from __future__ import annotations

from pathlib import Path

from nutev.querypacks.builders import build_queries
from nutev.settings import load_json


CONFIG_ROOT = Path(__file__).resolve().parents[1] / "config"


def test_metabolic_remission_supplement_is_merged_into_taxonomy() -> None:
    taxonomy = load_json(CONFIG_ROOT / "keyword_taxonomy.json")

    diet_terms = taxonomy["global"]["diet_patterns"]
    busca2a_terms = taxonomy["workstreams"]["busca2a"]["condition_terms"]
    busca2b_hints = taxonomy["workstreams"]["busca2b"]["web_query_hints"]

    assert "metabolic_remission_nutrition" in diet_terms
    assert "anti_obesity_pharmacotherapy_nutrition" in diet_terms
    assert "type 2 diabetes remission" in busca2a_terms
    assert "glp-1 receptor agonist nutrition" in busca2a_terms
    assert "obesity pharmacotherapy dietary adherence" in busca2b_hints


def test_busca2b_queries_include_metabolic_remission_and_pharmacotherapy_nutrition() -> None:
    taxonomy = load_json(CONFIG_ROOT / "keyword_taxonomy.json")
    queries = build_queries(taxonomy, "busca2b")
    rendered = "\n".join(queries).lower()

    assert "type 2 diabetes remission" in rendered
    assert "weight regain prevention" in rendered
    assert "glp-1 nutrition" in rendered
    assert "anti-obesity medication nutrition" in rendered
    assert "obesity pharmacotherapy nutrition care" in rendered
