from __future__ import annotations

from pathlib import Path

from nutev.querypacks.builders import build_structured_components
from nutev.settings import load_json


def _components_for(workstream: str) -> dict[str, list[str]]:
    taxonomy = load_json(Path("config/keyword_taxonomy.json"))
    _, components = build_structured_components(taxonomy, workstream)
    return components


def test_masld_nutrition_terms_expand_busca2a_guideline_queries() -> None:
    components = _components_for("busca2a")

    assert "MASLD nutrition" in components["condition_terms"]
    assert "MASLD clinical practice guideline" in components["web_hints"]
    assert "steatotic liver disease practice guidance" in components["web_hints"]


def test_masld_nutrition_terms_expand_busca2b_intervention_queries() -> None:
    components = _components_for("busca2b")

    assert "MASLD dietary intervention" in components["condition_terms"]
    assert "MASLD lifestyle intervention" in components["focus_terms"]
    assert "MASLD nutrition systematic review" in components["web_hints"]
    assert "lifestyle intervention trial" in components["doc_type_terms"]
