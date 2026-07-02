from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.querypacks.builders import build_querypack
from nutev.settings import load_json


def test_ckm_supplement_expands_busca2a_and_busca2b_queries() -> None:
    taxonomy = load_json(Path("config/keyword_taxonomy.json"))
    querypack = build_querypack(taxonomy, ["busca2a", "busca2b"])
    rendered = "\n".join(
        query.lower()
        for queries in querypack.values()
        for query in queries
    )

    assert "cardiovascular-kidney-metabolic syndrome" in rendered
    assert "cardiovascular kidney metabolic syndrome" in rendered
    assert "ckm syndrome" in rendered
    assert "ckm nutrition" in rendered
    assert "ckm lifestyle intervention" in rendered


def test_ckm_supplement_prioritizes_nutrition_relevant_busca2a_records() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Cardiovascular-kidney-metabolic syndrome nutrition guideline for obesity care",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2a",
    )
    baseline = score_record(
        {
            "title": "Nutrition guideline for obesity care",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2a",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])


def test_ckm_supplement_prioritizes_implementation_relevant_busca2b_records() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "CKM dietary adherence and lifestyle intervention trial for obesity",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    baseline = score_record(
        {
            "title": "Dietary adherence and lifestyle intervention trial for obesity",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])
