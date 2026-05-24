from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.settings import load_json


def _scoring_rules() -> dict:
    return load_json(Path("config") / "scoring_rules.json")


def test_hepatic_fat_measurement_terms_raise_busca2b_score() -> None:
    scoring_rules = _scoring_rules()
    baseline = {
        "title": "Dietary intervention for adult obesity and cardiometabolic risk",
        "abstract": "Adults received dietary counselling with metabolic follow-up.",
        "url": "https://example.org/article",
        "source": "pubmed",
        "journal": "",
        "source_institution": "",
    }
    enriched = {
        "title": "Dietary intervention for hepatic steatosis and cardiometabolic risk",
        "abstract": (
            "Adults with MASLD reduced intrahepatic fat and liver fat content "
            "during nutrition counselling follow-up."
        ),
        "url": "https://example.org/full-text.pdf",
        "source": "pubmed",
        "journal": "",
        "source_institution": "",
    }

    baseline_score = score_record(dict(baseline), scoring_rules, "busca2b")
    enriched_score = score_record(dict(enriched), scoring_rules, "busca2b")

    assert enriched_score["relevance_score"] > baseline_score["relevance_score"] + 10
    assert enriched_score["out_of_scope_flags"] == []


def test_liver_steatosis_variant_scores_above_generic_weight_follow_up() -> None:
    scoring_rules = _scoring_rules()
    baseline = {
        "title": "Adult weight follow-up after nutrition program",
        "abstract": "Adults received general lifestyle support and follow-up.",
        "url": "https://example.org/program",
        "source": "official",
        "journal": "",
        "source_institution": "",
    }
    enriched = {
        "title": "Lifestyle nutrition follow-up for liver steatosis in adults with obesity",
        "abstract": (
            "The program tracked hepatic steatosis, liver fat content and dietary adherence "
            "in adult obesity care."
        ),
        "url": "https://example.org/report.pdf",
        "source": "official",
        "journal": "",
        "source_institution": "",
    }

    baseline_score = score_record(dict(baseline), scoring_rules, "busca2b")
    enriched_score = score_record(dict(enriched), scoring_rules, "busca2b")

    assert enriched_score["relevance_score"] > baseline_score["relevance_score"] + 12
    assert enriched_score["out_of_scope_flags"] == []
