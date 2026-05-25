from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.settings import load_json


def _scoring_rules() -> dict:
    return load_json(Path("config") / "scoring_rules.json")


def test_mediterranean_dietary_pattern_variant_raises_busca2b_score() -> None:
    scoring_rules = _scoring_rules()
    baseline = {
        "title": "Diet intervention for obesity follow-up",
        "abstract": "Adults received general nutrition advice and metabolic follow-up.",
        "url": "https://example.org/article",
        "source": "pubmed",
        "journal": "",
        "source_institution": "",
    }
    enriched = {
        "title": "Mediterranean dietary pattern intervention for obesity and cardiometabolic risk",
        "abstract": (
            "Adults followed a Mediterranean dietary pattern with dietary adherence, "
            "blood pressure and lipid follow-up."
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


def test_dash_full_phrase_variant_raises_busca2a_score() -> None:
    scoring_rules = _scoring_rules()
    baseline = {
        "title": "Clinical nutrition guidance for hypertension follow-up",
        "abstract": "Adults received routine dietary advice for blood pressure care.",
        "url": "https://example.org/guidance",
        "source": "official",
        "journal": "",
        "source_institution": "",
    }
    enriched = {
        "title": "Dietary Approaches to Stop Hypertension guidance for cardiometabolic risk",
        "abstract": (
            "The guidance addresses hypertension, dyslipidemia and therapeutic lifestyle "
            "changes using the full DASH wording."
        ),
        "url": "https://example.org/guidance.pdf",
        "source": "official",
        "journal": "",
        "source_institution": "",
    }

    baseline_score = score_record(dict(baseline), scoring_rules, "busca2a")
    enriched_score = score_record(dict(enriched), scoring_rules, "busca2a")

    assert enriched_score["relevance_score"] > baseline_score["relevance_score"] + 8
    assert enriched_score["out_of_scope_flags"] == []


def test_non_hyphenated_plant_based_variant_raises_busca2b_score() -> None:
    scoring_rules = _scoring_rules()
    baseline = {
        "title": "Lifestyle nutrition program for obesity care",
        "abstract": "Adults received nutrition counselling and weight follow-up.",
        "url": "https://example.org/program",
        "source": "official",
        "journal": "",
        "source_institution": "",
    }
    enriched = {
        "title": "Plant based diet program for obesity and insulin resistance",
        "abstract": (
            "Adults followed a plant based diet with cardiometabolic follow-up and "
            "dietary adherence support."
        ),
        "url": "https://example.org/program.pdf",
        "source": "official",
        "journal": "",
        "source_institution": "",
    }

    baseline_score = score_record(dict(baseline), scoring_rules, "busca2b")
    enriched_score = score_record(dict(enriched), scoring_rules, "busca2b")

    assert enriched_score["relevance_score"] > baseline_score["relevance_score"] + 8
    assert enriched_score["out_of_scope_flags"] == []
