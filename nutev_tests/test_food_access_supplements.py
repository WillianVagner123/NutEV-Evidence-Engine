from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.settings import load_json


def test_food_access_supplement_expands_taxonomy_terms() -> None:
    taxonomy = load_json(Path("config/keyword_taxonomy.json"))
    busca2b_hints = taxonomy["workstreams"]["busca2b"]["web_query_hints"]
    contextual_terms = taxonomy["global"]["implementation_behavior"]["contextual"]

    assert "food insecurity intervention" in busca2b_hints
    assert "produce voucher program" in busca2b_hints
    assert "encaminhamento para segurança alimentar" in contextual_terms


def test_food_access_supplement_boosts_relevance_score() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Intervenção em insegurança alimentar com voucher de frutas e vegetais para obesidade e risco cardiometabólico",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    baseline = score_record(
        {
            "title": "Programa comunitário para obesidade e risco cardiometabólico",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])
