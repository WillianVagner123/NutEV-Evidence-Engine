from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.settings import load_json


def _score(title: str, workstream: str = "busca2b") -> float:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    record = score_record({"title": title, "source": "pubmed"}, scoring_rules, workstream)
    return float(record["relevance_score"])


def test_precision_nutrition_supplement_boosts_cardiometabolic_terms() -> None:
    boosted = _score(
        "Phenotype-guided nutrition and risk-stratified dietary intervention for cardiometabolic risk"
    )
    baseline = _score("Personalized nutrition intervention for cardiometabolic risk")

    assert boosted > baseline


def test_precision_noise_supplement_demotes_agriculture_and_bench_terms() -> None:
    scoped = _score("Precision nutrition intervention for type 2 diabetes and cardiometabolic risk")
    noisy = _score("Precision nutrition in livestock animal feed and soil microbiome metabolomics only")

    assert scoped > noisy
