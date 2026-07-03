from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.querypacks.builders import build_structured_components
from nutev.settings import load_json


def test_metabolic_remission_taxonomy_supplement_enriches_busca2_terms() -> None:
    taxonomy = load_json(Path("config/keyword_taxonomy.json"))
    _, components_2a = build_structured_components(taxonomy, "busca2a")
    _, components_2b = build_structured_components(taxonomy, "busca2b")

    assert "durable diabetes remission" in components_2a["condition_terms"]
    assert "diabetes remission consensus report" in components_2a["web_hints"]
    assert "weight regain prevention" in components_2b["focus_terms"]
    assert "weight loss maintenance systematic review" in components_2b["web_hints"]


def test_metabolic_remission_scoring_supplement_prioritizes_maintenance_items() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Weight loss maintenance trial for durable diabetes remission after intensive lifestyle intervention",
            "abstract": "Adults with obesity and cardiometabolic risk received dietary adherence and weight regain prevention support.",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    baseline = score_record(
        {
            "title": "Lifestyle intervention for adults with obesity and diabetes",
            "abstract": "Dietary adherence and cardiometabolic risk were evaluated.",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])
