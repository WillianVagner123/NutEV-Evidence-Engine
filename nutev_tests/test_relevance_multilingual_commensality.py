from pathlib import Path

from nutev.analysis.relevance import score_record
from nutev.settings import load_json


def _scoring_rules() -> dict:
    return load_json(Path("config") / "scoring_rules.json")


def test_scoring_rewards_portuguese_guideline_and_commensality_signals() -> None:
    scoring_rules = _scoring_rules()
    baseline = {
        "title": "Adult obesity nutrition framework",
        "abstract": "Lifestyle medicine support for healthy eating in adults.",
        "url": "https://example.org/report",
        "source": "official",
        "journal": "",
        "source_institution": "",
    }
    enriched = {
        "title": "Diretrizes alimentares e comensalidade em refeições em família para obesidade em adultos",
        "abstract": (
            "O documento aborda literacia alimentar, medicina culinária e comer junto "
            "como sinais de implementação em Medicina do Estilo de Vida."
        ),
        "url": "https://example.org/guideline.pdf",
        "source": "official",
        "journal": "",
        "source_institution": "Ministério da Saúde",
    }

    baseline_score = score_record(dict(baseline), scoring_rules, "busca1")
    enriched_score = score_record(dict(enriched), scoring_rules, "busca1")

    assert enriched_score["relevance_score"] > baseline_score["relevance_score"] + 15
    assert enriched_score["out_of_scope_flags"] == []


def test_scoring_rewards_food_literacy_and_social_eating_variants_for_a3() -> None:
    scoring_rules = _scoring_rules()
    baseline = {
        "title": "Adult lifestyle medicine framework",
        "abstract": "Framework for nutrition behavior in adults.",
        "url": "https://example.org/framework",
        "source": "official",
        "journal": "",
        "source_institution": "",
    }
    enriched = {
        "title": "Food literacy, social eating and family meals questionnaire for adults",
        "abstract": (
            "The instrument covers eat together routines, commensality and culinary medicine "
            "for lifestyle medicine practice."
        ),
        "url": "https://example.org/framework.pdf",
        "source": "official",
        "journal": "",
        "source_institution": "",
    }

    baseline_score = score_record(dict(baseline), scoring_rules, "artigo3_framework")
    enriched_score = score_record(dict(enriched), scoring_rules, "artigo3_framework")

    assert enriched_score["relevance_score"] > baseline_score["relevance_score"] + 10
    assert enriched_score["out_of_scope_flags"] == []
