from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.settings import load_json


def _score(title: str, workstream: str = "busca2b") -> float:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    record = score_record(
        {
            "title": title,
            "source": "pubmed",
            "abstract": "Adult obesity and type 2 diabetes nutrition care with lifestyle intervention support.",
        },
        scoring_rules,
        workstream,
    )
    return float(record["relevance_score"])


def test_weight_recurrence_terms_gain_busca2b_priority() -> None:
    boosted = _score(
        "Randomized trial of post-weight-loss maintenance to prevent weight recurrence in adult obesity"
    )
    baseline = _score(
        "Randomized trial of lifestyle intervention follow-up in adult obesity"
    )

    assert boosted > baseline


def test_diabetes_remission_relapse_terms_gain_busca2b_priority() -> None:
    boosted = _score(
        "Dietary intervention for durable diabetes remission and relapse after diabetes remission in adult obesity"
    )
    baseline = _score(
        "Dietary intervention for diabetes remission in adult obesity"
    )

    assert boosted > baseline


def test_diabetes_remission_durability_terms_gain_busca2a_priority() -> None:
    boosted = _score(
        "Consensus guidance on sustained diabetes remission and loss of diabetes remission in type 2 diabetes",
        workstream="busca2a",
    )
    baseline = _score(
        "Consensus guidance on diabetes remission in type 2 diabetes",
        workstream="busca2a",
    )

    assert boosted > baseline
