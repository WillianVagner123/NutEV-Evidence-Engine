from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.settings import load_json


def test_sports_performance_focus_is_downranked_for_busca2b() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))

    clinical_nutmev_record = score_record(
        {
            "title": "High protein dietary pattern for adult obesity and cardiometabolic risk",
            "abstract": "Lifestyle nutrition intervention with dietary adherence outcomes.",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    sports_noise_record = score_record(
        {
            "title": "High protein diet and sports performance in resistance-trained athletes",
            "abstract": "Sports nutrition trial focused on exercise performance and muscle hypertrophy.",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert sports_noise_record["relevance_score"] < clinical_nutmev_record["relevance_score"]


def test_sports_noise_supplement_preserves_clinical_obesity_signal() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))

    clinical_with_exercise = score_record(
        {
            "title": "Lifestyle intervention with diet and exercise for adult obesity and diabetes",
            "abstract": "Dietary adherence, cardiometabolic risk, and medical nutrition therapy.",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    sports_noise_record = score_record(
        {
            "title": "Sports nutrition supplement for elite athletes and exercise performance",
            "abstract": "Ergogenic aid study in competitive athletes.",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert clinical_with_exercise["relevance_score"] > sports_noise_record["relevance_score"]
