from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.settings import load_json


def _score(title: str, workstream: str) -> float:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    record = score_record({"title": title, "source": "pubmed"}, scoring_rules, workstream)
    return float(record["relevance_score"])


def test_precision_nutrition_gains_busca2a_priority() -> None:
    boosted = _score(
        "Precision nutrition framework for obesity, type 2 diabetes and cardiometabolic risk",
        "busca2a",
    )
    baseline = _score(
        "Nutrition framework for obesity, type 2 diabetes and cardiometabolic risk",
        "busca2a",
    )

    assert boosted > baseline


def test_tailored_dietary_intervention_gains_busca2b_priority() -> None:
    boosted = _score(
        "Personalized dietary intervention for obesity, insulin resistance and dietary adherence",
        "busca2b",
    )
    baseline = _score(
        "Dietary intervention for obesity, insulin resistance and dietary adherence",
        "busca2b",
    )

    assert boosted > baseline


def test_personalized_nutrition_framework_gains_article3_priority() -> None:
    boosted = _score(
        "Personalized nutrition framework for food literacy and behavior change",
        "artigo3_framework",
    )
    baseline = _score(
        "Nutrition framework for food literacy and behavior change",
        "artigo3_framework",
    )

    assert boosted > baseline
