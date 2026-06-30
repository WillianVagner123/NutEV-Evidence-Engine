from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.settings import load_json


def test_preclinical_noise_terms_are_loaded_with_negative_points() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    keyword_points = scoring_rules["keyword_points"]

    assert keyword_points["murine"] < 0
    assert keyword_points["cell line"] < 0
    assert keyword_points["gene expression"] < 0


def test_preclinical_noise_terms_reduce_priority_when_nutmev_terms_match() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    clean = score_record(
        {
            "title": "Medical nutrition therapy for obesity and cardiometabolic risk",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    noisy = score_record(
        {
            "title": "Murine cell line gene expression study of medical nutrition therapy for obesity and cardiometabolic risk",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert float(noisy["relevance_score"]) < float(clean["relevance_score"])
