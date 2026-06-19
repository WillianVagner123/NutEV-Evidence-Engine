from __future__ import annotations

from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.settings import load_json


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


def test_expanded_mash_term_gains_busca2b_priority() -> None:
    boosted = _score(
        "Lifestyle intervention for metabolic dysfunction-associated steatohepatitis in obesity"
    )
    baseline = _score("Lifestyle intervention for steatohepatitis in obesity")

    assert boosted > baseline


def test_portuguese_lifestyle_medicine_phrase_gains_busca2a_priority() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Medicina do estilo de vida e diretriz clínica para obesidade e diabetes tipo 2",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2a",
    )
    baseline = score_record(
        {
            "title": "Diretriz clínica para obesidade e diabetes tipo 2",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2a",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])


def test_configured_food_access_program_bonus_gains_busca2b_priority() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Healthy food incentive program for obesity and cardiometabolic risk",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    baseline = score_record(
        {
            "title": "Community food support program for obesity and cardiometabolic risk",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])


def test_configured_nutrition_care_delivery_bonus_gains_busca2b_priority() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Dietitian-delivered intervention with nutrition care pathway for obesity and cardiometabolic risk",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    baseline = score_record(
        {
            "title": "Dietitian-led intervention for obesity and cardiometabolic risk",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])


def test_configured_busca2a_advanced_dyslipidemia_bonus_gains_priority() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Clinical practice guideline for obesity with hypertriglyceridemia, apolipoprotein B, and remnant cholesterol management",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2a",
    )
    baseline = score_record(
        {
            "title": "Clinical practice guideline for obesity with lipid management",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2a",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])


def test_configured_busca2b_advanced_dyslipidemia_bonus_gains_priority() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Randomized trial of Mediterranean diet for clinical obesity with apo B and remnant cholesterol reduction",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    baseline = score_record(
        {
            "title": "Randomized trial of Mediterranean diet for obesity with lipid reduction",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])


def test_configured_cardiometabolic_diet_quality_terms_gain_busca2b_priority() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Randomized trial of low glycemic index anti-inflammatory diet for obesity and cardiometabolic risk",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    baseline = score_record(
        {
            "title": "Randomized trial of healthy diet for obesity and cardiometabolic risk",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"])
