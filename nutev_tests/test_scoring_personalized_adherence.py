from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.settings import load_json


def test_personalized_adherence_terms_are_loaded_into_scoring_rules() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))

    for term in [
        "personalized nutrition",
        "personalised nutrition",
        "precision nutrition",
        "tailored dietary intervention",
        "individualized dietary intervention",
        "individualised dietary intervention",
        "patient-centered nutrition care",
        "patient centred nutrition care",
        "remote nutrition coaching",
        "digital nutrition intervention",
        "dietary self-regulation",
        "implementation intentions",
    ]:
        assert term in scoring_rules["keyword_points"]


def test_personalized_adherence_signals_gain_busca2b_priority() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Tailored dietary intervention with personalized nutrition coaching for obesity and type 2 diabetes",
            "abstract": "Patient-centered nutrition care used shared decision making nutrition, dietary self-monitoring, and relapse prevention support.",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )
    baseline = score_record(
        {
            "title": "Dietary intervention for obesity and type 2 diabetes",
            "abstract": "Lifestyle counseling and adherence support were provided.",
            "source": "pubmed",
        },
        scoring_rules,
        "busca2b",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"]) + 15


def test_personalized_adherence_framework_signals_gain_a3_priority() -> None:
    scoring_rules = load_json(Path("config/scoring_rules.json"))
    boosted = score_record(
        {
            "title": "Precision nutrition framework for shared decision making nutrition and dietary self-regulation",
            "abstract": "The framework maps patient-centered nutrition care, implementation intentions, and habit formation.",
            "source": "pubmed",
        },
        scoring_rules,
        "artigo3_framework",
    )
    baseline = score_record(
        {
            "title": "Nutrition framework for dietary behavior change",
            "abstract": "The framework maps general adherence domains.",
            "source": "pubmed",
        },
        scoring_rules,
        "artigo3_framework",
    )

    assert float(boosted["relevance_score"]) > float(baseline["relevance_score"]) + 10
