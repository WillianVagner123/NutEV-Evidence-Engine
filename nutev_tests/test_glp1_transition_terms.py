from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.querypacks.provider_queries import build_provider_querypack
from nutev.settings import load_json


def test_glp1_nutrition_transition_terms_enter_busca2b_provider_queries() -> None:
    taxonomy = load_json(Path("config/keyword_taxonomy.json"))
    querypack = build_provider_querypack(
        taxonomy,
        ["busca2b"],
        {"busca2b": ["pubmed"]},
    )
    rendered = "\n".join(querypack["busca2b"]["pubmed"]).lower()

    assert "weight regain after glp-1 discontinuation" in rendered
    assert "nutrition counseling during glp-1 therapy" in rendered


def test_glp1_nutrition_transition_scores_above_pharmacology_only_match() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Nutrition counseling during GLP-1 therapy for adults with obesity and cardiometabolic risk",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    baseline = score_record(
        {
            "title": "GLP-1 receptor agonist therapy for adults with obesity",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])
