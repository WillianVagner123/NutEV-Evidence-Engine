from __future__ import annotations

from pathlib import Path

from nutev.querypacks import BEHAVIOR_CHANGE_MODEL_TERMS
from nutev.querypacks.builders import build_structured_components
from nutev.settings import load_json


def test_busca2b_includes_behavior_change_model_terms_in_search_components() -> None:
    keyword_taxonomy = load_json(Path("config/keyword_taxonomy.json"))
    _, components = build_structured_components(keyword_taxonomy, "busca2b")
    joined_focus = " ".join(components["focus_terms"]).lower()
    joined_hints = " ".join(components["web_hints"]).lower()

    assert "behavior change technique" in joined_focus
    assert "behavior change wheel" in joined_hints
    assert "com-b" in joined_hints
    assert "implementation mapping" in joined_focus


def test_artigo3_includes_behavior_change_model_terms_in_search_components() -> None:
    keyword_taxonomy = load_json(Path("config/keyword_taxonomy.json"))
    _, components = build_structured_components(keyword_taxonomy, "artigo3_framework")
    joined_focus = " ".join(components["focus_terms"]).lower()
    joined_hints = " ".join(components["web_hints"]).lower()

    assert "behavior change technique" in joined_focus
    assert "behaviour change techniques" in joined_hints
    assert "capability opportunity motivation behavior" in joined_focus
    assert "self-management support" in joined_hints


def test_behavior_change_model_terms_are_unique_case_insensitive() -> None:
    lowered = [term.lower() for term in BEHAVIOR_CHANGE_MODEL_TERMS]

    assert len(lowered) == len(set(lowered))
