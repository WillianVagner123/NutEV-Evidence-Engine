from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.settings import load_json


def _configured_score(title: str, workstream: str) -> float:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    record = score_record({"title": title, "source": "pubmed"}, scoring_rules, workstream)
    return float(record["relevance_score"])


def test_social_prescribing_food_access_terms_gain_busca1_priority() -> None:
    boosted = _configured_score(
        "Social prescribing food pharmacy referral program for obesity and healthy food access",
        "busca1",
    )
    baseline = _configured_score(
        "Community support program for obesity and healthy food access",
        "busca1",
    )

    assert boosted > baseline


def test_social_prescribing_food_access_terms_gain_busca2b_priority() -> None:
    boosted = _configured_score(
        "Social prescribing food pharmacy referral intervention for dietary adherence and cardiometabolic risk",
        "busca2b",
    )
    baseline = _configured_score(
        "Community support intervention for dietary adherence and cardiometabolic risk",
        "busca2b",
    )

    assert boosted > baseline
