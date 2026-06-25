from __future__ import annotations

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.settings import load_json


def test_culinary_literacy_supplement_terms_merge_into_taxonomy() -> None:
    taxonomy = load_json("config/keyword_taxonomy.json")

    culinary_terms = taxonomy["global"]["nutrition_domains"]["culinary_labeling"]
    busca1_hints = taxonomy["workstreams"]["busca1"]["web_query_hints"]
    busca2b_hints = taxonomy["workstreams"]["busca2b"]["web_query_hints"]

    assert "culinary medicine curriculum" in culinary_terms
    assert "food literacy intervention" in culinary_terms
    assert "teaching kitchen evaluation" in busca1_hints
    assert "cooking self-efficacy scale" in busca2b_hints


def test_culinary_literacy_supplement_terms_render_in_provider_queries() -> None:
    taxonomy = load_json("config/keyword_taxonomy.json")

    busca1_queries = "\n".join(render_queries_for_provider(taxonomy, "busca1", "pubmed")).lower()
    busca2b_queries = "\n".join(render_queries_for_provider(taxonomy, "busca2b", "pubmed")).lower()

    assert "culinary medicine curriculum" in busca1_queries
    assert "food literacy intervention" in busca1_queries
    assert "culinary nutrition intervention" in busca2b_queries
    assert "cooking self-efficacy scale" in busca2b_queries


def test_culinary_literacy_scoring_supplement_terms_merge() -> None:
    scoring = load_json("config/scoring_rules.json")

    assert scoring["keyword_points"]["culinary medicine curriculum"] == 4
    assert scoring["keyword_points"]["food literacy intervention"] == 4
    assert scoring["workstream_bonus"]["busca1"]["teaching kitchen evaluation"] == 5
    assert scoring["workstream_bonus"]["artigo3_framework"]["food literacy scale"] == 5
