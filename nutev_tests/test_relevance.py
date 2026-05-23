from __future__ import annotations

from nutev.analysis.relevance import score_record


EMPTY_SCORING_RULES = {
    "keyword_points": {},
    "source_points": {},
    "workstream_points": {},
    "editorial_authority_points": {},
}


def _score(title: str, workstream: str = "busca2b") -> float:
    record = score_record({"title": title, "source": "pubmed"}, EMPTY_SCORING_RULES, workstream)
    return float(record["relevance_score"])


def test_food_prescription_variants_gain_busca2b_priority() -> None:
    boosted = _score(
        "Fruit and vegetable prescription program for obesity and cardiometabolic risk"
    )
    baseline = _score("Obesity and cardiometabolic risk program")

    assert boosted > baseline


def test_produce_rx_variant_gains_busca1_priority() -> None:
    boosted = _score(
        "Produce Rx and medically tailored meals in food-based dietary guidance",
        workstream="busca1",
    )
    baseline = _score("Food-based dietary guidance for obesity", workstream="busca1")

    assert boosted > baseline


def test_implementation_delivery_signals_gain_busca2b_priority() -> None:
    boosted = _score(
        "Audit and feedback with practice facilitation for dietary adherence implementation"
    )
    baseline = _score("Dietary adherence implementation")

    assert boosted > baseline
