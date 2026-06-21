from pathlib import Path

from nutev.querypacks.builders import build_structured_components
from nutev.settings import load_json


def _taxonomy() -> dict:
    return load_json(Path(__file__).resolve().parents[1] / "config" / "keyword_taxonomy.json")


def test_ckm_terms_are_explicit_busca2a_conditions_after_supplements() -> None:
    _, components = build_structured_components(_taxonomy(), "busca2a")
    condition_terms = {term.lower() for term in components["condition_terms"]}
    focus_terms = {term.lower() for term in components["focus_terms"]}
    web_hints = {term.lower() for term in components["web_hints"]}

    assert "cardiovascular-kidney-metabolic syndrome" in condition_terms
    assert "cardiovascular kidney metabolic syndrome" in condition_terms
    assert "ckm syndrome" in condition_terms
    assert "ckm nutrition" in focus_terms
    assert "ckm syndrome guideline" in web_hints


def test_ckm_terms_are_explicit_busca2b_conditions_after_supplements() -> None:
    _, components = build_structured_components(_taxonomy(), "busca2b")
    condition_terms = {term.lower() for term in components["condition_terms"]}
    focus_terms = {term.lower() for term in components["focus_terms"]}
    web_hints = {term.lower() for term in components["web_hints"]}

    assert "cardiovascular-kidney-metabolic syndrome" in condition_terms
    assert "cardiovascular kidney metabolic risk" in condition_terms
    assert "ckm risk" in condition_terms
    assert "ckm nutrition intervention" in focus_terms
    assert "ckm syndrome lifestyle intervention" in web_hints
