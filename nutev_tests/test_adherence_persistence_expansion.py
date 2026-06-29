from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.settings import load_json


def test_adherence_persistence_supplement_reaches_busca2b_provider_queries() -> None:
    taxonomy = load_json(Path("config/keyword_taxonomy.json"))
    queries = render_queries_for_provider(taxonomy, "busca2b", "pubmed")
    query_text = "\n".join(queries).lower()

    assert "meal plan adherence" in query_text
    assert "weight self-monitoring" in query_text
    assert "diet acceptability" in query_text


def test_adherence_persistence_supplement_gains_busca2b_priority() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": (
                "Meal plan adherence with weight self-monitoring during the "
                "maintenance phase after lifestyle intervention for obesity"
            ),
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    baseline = score_record(
        {
            "title": "Lifestyle intervention for obesity maintenance",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])
