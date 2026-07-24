from pathlib import Path

from nutev.settings import load_json


CONFIG_ROOT = Path(__file__).resolve().parents[1] / "config"


def test_keyword_taxonomy_supplement_adds_adiposity_terms_to_busca2b() -> None:
    taxonomy = load_json(CONFIG_ROOT / "keyword_taxonomy.json")

    busca2b_terms = {term.lower() for term in taxonomy["workstreams"]["busca2b"]["condition_terms"]}
    obesity_terms = {term.lower() for term in taxonomy["clinical"]["obesity"]}
    anthropometry_terms = {term.lower() for term in taxonomy["outcomes"]["anthropometry"]}

    assert "central adiposity" in busca2b_terms
    assert "cardiometabolic multimorbidity" in busca2b_terms
    assert "waist-to-height ratio" in obesity_terms
    assert "visceral adiposity" in anthropometry_terms


def test_scoring_supplement_prioritizes_cardiometabolic_adiposity_terms() -> None:
    scoring_rules = load_json(CONFIG_ROOT / "scoring_rules.json")

    assert scoring_rules["keyword_points"]["cardiometabolic multimorbidity"] == 4
    assert scoring_rules["keyword_points"]["central adiposity"] == 3
    assert scoring_rules["workstream_bonus"]["busca2a"]["waist-to-height ratio"] == 4
    assert scoring_rules["workstream_bonus"]["busca2b"]["visceral adiposity"] == 4
