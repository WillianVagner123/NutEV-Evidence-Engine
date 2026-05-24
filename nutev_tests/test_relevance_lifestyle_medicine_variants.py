from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.settings import load_json


def _scoring_rules() -> dict:
    return load_json(Path("config") / "scoring_rules.json")


def test_lifestyle_medicine_intervention_variant_raises_busca2b_score() -> None:
    scoring_rules = _scoring_rules()
    baseline = {
        "title": "Adult obesity nutrition follow-up",
        "abstract": "Adults received routine dietary advice with weight follow-up.",
        "url": "https://example.org/article",
        "source": "pubmed",
        "journal": "",
        "source_institution": "",
    }
    enriched = {
        "title": "Lifestyle medicine intervention for obesity and cardiometabolic risk",
        "abstract": (
            "Adults completed a lifestyle medicine program with dietary adherence, "
            "behavior change support and metabolic follow-up."
        ),
        "url": "https://example.org/full-text.pdf",
        "source": "pubmed",
        "journal": "",
        "source_institution": "",
    }

    baseline_score = score_record(dict(baseline), scoring_rules, "busca2b")
    enriched_score = score_record(dict(enriched), scoring_rules, "busca2b")

    assert enriched_score["relevance_score"] > baseline_score["relevance_score"] + 12
    assert enriched_score["out_of_scope_flags"] == []


def test_lifestyle_medicine_counselling_variant_raises_busca1_score() -> None:
    scoring_rules = _scoring_rules()
    baseline = {
        "title": "Community healthy eating report",
        "abstract": "Adults discussed general food choices.",
        "url": "https://example.org/report",
        "source": "official",
        "journal": "",
        "source_institution": "",
    }
    enriched = {
        "title": "Lifestyle medicine counselling approach for adult obesity prevention",
        "abstract": (
            "The report covers food literacy, meal planning and nutrition counselling "
            "for community adults."
        ),
        "url": "https://example.org/guidance.pdf",
        "source": "official",
        "journal": "",
        "source_institution": "",
    }

    baseline_score = score_record(dict(baseline), scoring_rules, "busca1")
    enriched_score = score_record(dict(enriched), scoring_rules, "busca1")

    assert enriched_score["relevance_score"] > baseline_score["relevance_score"] + 10
    assert enriched_score["out_of_scope_flags"] == []
