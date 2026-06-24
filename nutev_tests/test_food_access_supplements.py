from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.querypacks.builders import build_querypack
from nutev.settings import load_json


def test_food_access_supplement_expands_busca2b_queries() -> None:
    taxonomy = load_json(Path("config/keyword_taxonomy.json"))
    querypack = build_querypack(taxonomy, ["busca2b"])
    queries_text = "\n".join(querypack["busca2b"]).lower()

    assert "food insecurity intervention" in queries_text
    assert "produce voucher program" in queries_text


def test_food_access_supplement_boosts_relevance_score() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Food insecurity intervention with produce voucher program for obesity and cardiometabolic risk",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    baseline = score_record(
        {
            "title": "Community support program for obesity and cardiometabolic risk",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])
