from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.settings import load_json


CONFIG_ROOT = Path(__file__).resolve().parents[1] / "config"


def test_cardiometabolic_precision_supplement_is_loaded() -> None:
    scoring = load_json(CONFIG_ROOT / "scoring_rules.json")

    assert scoring["keyword_points"]["type 2 diabetes"] == 3
    assert scoring["keyword_points"]["diet quality"] == 3
    assert scoring["workstream_bonus"]["busca2b"]["sodium reduction"] == 4


def test_cardiometabolic_precision_terms_increase_relevance_score() -> None:
    record = {
        "title": "Type 2 diabetes diet quality intervention with glycaemic control outcomes",
        "abstract": "Randomized trial reporting LDL cholesterol and blood pressure reduction.",
        "source": "openalex",
    }
    base_scoring = {
        "keyword_points": {},
        "source_points": {},
        "workstream_points": {},
    }
    supplemented_scoring = load_json(CONFIG_ROOT / "scoring_rules.json")

    base_score = score_record(dict(record), base_scoring, "busca2b")["relevance_score"]
    supplemented_score = score_record(
        dict(record),
        supplemented_scoring,
        "busca2b",
    )["relevance_score"]

    assert supplemented_score >= base_score + 20
