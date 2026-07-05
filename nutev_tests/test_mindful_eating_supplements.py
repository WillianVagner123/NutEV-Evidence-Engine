from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.settings import load_json


def test_mindful_eating_terms_are_loaded_from_taxonomy_supplement() -> None:
    taxonomy = load_json(Path("config/keyword_taxonomy.json"))

    behavioral_terms = taxonomy["global"]["implementation_behavior"]["behavioral"]
    busca2b_hints = taxonomy["workstreams"]["busca2b"]["web_query_hints"]

    assert "mindful eating" in behavioral_terms
    assert "intuitive eating intervention" in behavioral_terms
    assert "portion control intervention" in busca2b_hints


def test_mindful_eating_gains_busca2b_priority() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Mindful eating intervention for adults with obesity and cardiometabolic risk",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    baseline = score_record(
        {
            "title": "Dietary education for adults with obesity and cardiometabolic risk",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])


def test_intuitive_eating_instrument_gains_a3_priority() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Intuitive eating scale and eating self-regulation questionnaire validation",
            "source": "pubmed",
        },
        scoring_rules,
        "artigo3_framework",
    )
    baseline = score_record(
        {
            "title": "Eating questionnaire validation",
            "source": "pubmed",
        },
        scoring_rules,
        "artigo3_framework",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])
