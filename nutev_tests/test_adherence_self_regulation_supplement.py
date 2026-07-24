from __future__ import annotations

from pathlib import Path

from nutev.querypacks.builders import build_structured_components
from nutev.settings import load_json


def test_adherence_self_regulation_supplement_is_loaded() -> None:
    taxonomy = load_json(Path("config/keyword_taxonomy.json"))

    terms = taxonomy["global"]["implementation_behavior"]["adherence_self_regulation"]
    assert "dietary self-monitoring" in terms
    assert "dietary implementation intentions" in terms
    assert "dietary problem solving" in terms

    outcomes = taxonomy["outcomes"]["diet_quality_adherence"]
    assert "dietary habit formation" in outcomes
    assert "dietary lapse management" in outcomes


def test_adherence_self_regulation_terms_enter_query_components() -> None:
    taxonomy = load_json(Path("config/keyword_taxonomy.json"))
    _, busca2b = build_structured_components(taxonomy, "busca2b")
    _, framework = build_structured_components(taxonomy, "artigo3_framework")

    busca2b_behavior = " ".join(busca2b["behavior_terms"]).lower()
    busca2b_hints = " ".join(busca2b["web_hints"]).lower()
    framework_hints = " ".join(framework["web_hints"]).lower()

    assert "dietary self-monitoring" in busca2b_behavior
    assert "dietary problem solving intervention" in busca2b_hints
    assert "dietary self-regulation scale" in framework_hints
