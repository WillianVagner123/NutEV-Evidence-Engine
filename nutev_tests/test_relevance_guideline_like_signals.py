from __future__ import annotations

from nutev.analysis.relevance import score_record


EMPTY_SCORING_RULES = {
    "keyword_points": {},
    "source_points": {},
    "workstream_points": {},
    "editorial_authority_points": {},
}


def _score(title: str, workstream: str = "busca2a") -> float:
    record = score_record({"title": title, "source": "pubmed"}, EMPTY_SCORING_RULES, workstream)
    return float(record["relevance_score"])


def test_policy_statement_gains_busca2a_priority() -> None:
    boosted = _score("Policy statement for lifestyle medicine in obesity and MASLD")
    baseline = _score("Clinical document for lifestyle medicine in obesity and MASLD")

    assert boosted > baseline


def test_nutrition_practice_guideline_gains_busca2a_priority() -> None:
    boosted = _score(
        "Nutrition practice guideline for obesity, diabetes, and cardiometabolic risk"
    )
    baseline = _score(
        "Nutrition clinical document for obesity, diabetes, and cardiometabolic risk"
    )

    assert boosted > baseline


def test_consensus_update_gains_busca2a_priority() -> None:
    boosted = _score(
        "Consensus update for clinical obesity and dyslipidemia management"
    )
    baseline = _score(
        "Clinical update for obesity and dyslipidemia management"
    )

    assert boosted > baseline
