from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.settings import load_json


def test_glp1_nutrition_bridge_terms_reach_provider_queries() -> None:
    taxonomy = load_json(Path("config/keyword_taxonomy.json"))

    queries = render_queries_for_provider(taxonomy, "busca2b", "pubmed")
    query_text = "\n".join(queries).lower()

    assert "semaglutide" in query_text
    assert "dietary adherence" in query_text


def test_glp1_nutrition_bridge_scores_above_isolated_drug_mention() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    isolated = score_record(
        {
            "title": "Semaglutide for obesity and cardiometabolic risk",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    bridged = score_record(
        {
            "title": "Semaglutide dietary adherence and lifestyle intervention for obesity and cardiometabolic risk",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert float(bridged["relevance_score"]) > float(isolated["relevance_score"])
