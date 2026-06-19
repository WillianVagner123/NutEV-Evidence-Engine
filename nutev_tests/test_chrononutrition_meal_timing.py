from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.settings import load_json


def test_chrononutrition_terms_reach_provider_queries() -> None:
    taxonomy = load_json(Path("config/keyword_taxonomy.json"))

    queries = render_queries_for_provider(taxonomy, "busca2b", "pubmed")
    query_text = "\n".join(queries).lower()

    assert "chrononutrition" in query_text
    assert "early time-restricted eating" in query_text
    assert "eating window adherence" in query_text


def test_chrononutrition_intervention_scores_above_generic_meal_timing() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    generic = score_record(
        {
            "title": "Meal timing and dietary habits in adults",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    focused = score_record(
        {
            "title": "Early time-restricted eating trial for obesity and cardiometabolic risk with eating window adherence",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert float(focused["relevance_score"]) > float(generic["relevance_score"])
