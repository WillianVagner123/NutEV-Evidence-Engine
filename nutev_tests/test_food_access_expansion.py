from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.querypacks.builders import build_queries
from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.settings import load_json


def test_food_access_supplement_terms_reach_master_and_provider_querypacks() -> None:
    taxonomy = load_json(Path("config/keyword_taxonomy.json"))

    master_queries = "\n".join(build_queries(taxonomy, "busca2b")).lower()
    pubmed_queries = "\n".join(
        render_queries_for_provider(taxonomy, "busca2b", "pubmed")
    ).lower()

    assert "grocery prescription" in master_queries
    assert "food pharmacy intervention" in master_queries
    assert "food farmacy" in pubmed_queries


def test_food_access_prescription_terms_gain_busca2b_priority() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Grocery prescription program for adults with obesity and cardiometabolic risk",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    baseline = score_record(
        {
            "title": "Community grocery program for adults with obesity and cardiometabolic risk",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])
