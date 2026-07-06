from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.querypacks.provider_queries import build_provider_querypack
from nutev.settings import load_json


def test_digital_nutrition_terms_are_added_to_busca2b_provider_queries() -> None:
    taxonomy = load_json(Path("config/keyword_taxonomy.json"))
    querypack = build_provider_querypack(
        taxonomy,
        ["busca2b"],
        {"busca2b": ["pubmed", "europepmc"]},
    )
    rendered = "\n".join(
        query
        for provider_queries in querypack["busca2b"].values()
        for query in provider_queries
    ).lower()

    assert "digital diabetes prevention program" in rendered
    assert "remote nutrition coaching" in rendered
    assert "mobile dietary self-monitoring" in rendered


def test_digital_nutrition_scoring_prioritizes_remote_adherence_interventions() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Digital diabetes prevention program with remote nutrition coaching and mobile dietary self-monitoring for adults with obesity",
            "abstract": "Cardiometabolic risk intervention focused on dietary adherence and weight loss maintenance",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    baseline = score_record(
        {
            "title": "Diabetes prevention program for adults with obesity",
            "abstract": "Cardiometabolic risk intervention focused on dietary adherence and weight loss maintenance",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])


def test_digital_food_diary_gains_article3_framework_priority() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Digital food diary and app-based food diary for dietary adherence questionnaire validation",
            "source": "pubmed",
        },
        scoring_rules,
        "artigo3_framework",
    )
    baseline = score_record(
        {
            "title": "Food diary for dietary adherence questionnaire validation",
            "source": "pubmed",
        },
        scoring_rules,
        "artigo3_framework",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])
