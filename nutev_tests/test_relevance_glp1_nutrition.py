from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.settings import load_json


def test_glp1_nutrition_guidance_gains_busca2a_priority() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": (
                "Clinical practice guideline for anti-obesity medication nutrition care "
                "and GLP-1 receptor agonist dietary counseling"
            ),
            "abstract": "Adults with obesity and cardiometabolic risk received nutrition care guidance.",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2a",
    )
    baseline = score_record(
        {
            "title": "Clinical practice guideline for anti-obesity medication management",
            "abstract": "Adults with obesity and cardiometabolic risk received routine care guidance.",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2a",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])
    assert boosted["out_of_scope_flags"] == []


def test_glp1_protein_and_lean_mass_terms_gain_busca2b_priority() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": (
                "GLP-1 nutrition intervention with protein adequacy and lean mass "
                "preservation for adults with obesity"
            ),
            "abstract": (
                "The dietitian-led intervention evaluated dietary adherence, muscle "
                "preservation and cardiometabolic outcomes during incretin therapy."
            ),
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    baseline = score_record(
        {
            "title": "GLP-1 follow-up for adults with obesity",
            "abstract": "Adults with obesity received routine follow-up during medication therapy.",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])
    assert boosted["out_of_scope_flags"] == []
