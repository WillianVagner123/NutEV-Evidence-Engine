from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.settings import load_json


def test_food_access_supplement_expands_busca2b_provider_queries() -> None:
    taxonomy = load_json(Path("config/keyword_taxonomy.json"))

    queries = render_queries_for_provider(taxonomy, "busca2b", "pubmed")
    joined = "\n".join(queries).lower()

    assert "food farmacy program" in joined
    assert "closed-loop referral" in joined or "closed loop referral" in joined
    assert "nutrition security referral" in joined


def test_food_access_supplement_prioritizes_referral_intervention() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Food farmacy program with closed-loop referral for adults with obesity and cardiometabolic risk",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    baseline = score_record(
        {
            "title": "Community support program for adults with obesity and cardiometabolic risk",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])
