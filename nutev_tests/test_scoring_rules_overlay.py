from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.settings import load_json


def _score_with_config(title: str, workstream: str = "busca2b") -> float:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    record = score_record({"title": title, "source": "pubmed"}, scoring_rules, workstream)
    return float(record["relevance_score"])


def test_scoring_rules_overlay_is_merged() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))

    assert scoring_rules["keyword_points"]["healthy eating index"] == 3
    assert scoring_rules["workstream_bonus"]["busca2b"]["dietary pattern adherence"] == 5


def test_diet_quality_indices_gain_busca2b_priority() -> None:
    boosted = _score_with_config(
        "Healthy eating index and Mediterranean diet adherence score in obesity care"
    )
    baseline = _score_with_config("Dietary assessment in obesity care")

    assert boosted > baseline


def test_diet_quality_scores_gain_framework_priority() -> None:
    boosted = _score_with_config(
        "Diet quality score instrument for dietary adherence in lifestyle medicine",
        workstream="artigo3_framework",
    )
    baseline = _score_with_config(
        "Dietary adherence instrument for lifestyle medicine",
        workstream="artigo3_framework",
    )

    assert boosted > baseline
