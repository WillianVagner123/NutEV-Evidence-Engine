from __future__ import annotations

from pathlib import Path

from nutev.querypacks.builders import build_structured_components
from nutev.settings import load_json


SUPPLEMENT_PATH = Path("config/keyword_taxonomy_supplement_anti_obesity_nutrition.json")
ANCHORS = (
    "nutrition",
    "dietary",
    "dietitian",
    "meal planning",
    "protein intake",
    "lean mass preservation",
)


def test_anti_obesity_nutrition_supplement_terms_are_nutrition_anchored() -> None:
    supplement = load_json(SUPPLEMENT_PATH)
    terms = supplement["global"]["implementation_behavior"][
        "anti_obesity_nutrition_care"
    ]

    assert terms
    assert all(any(anchor in term.lower() for anchor in ANCHORS) for term in terms)


def test_busca2a_receives_guideline_oriented_anti_obesity_nutrition_terms() -> None:
    taxonomy = load_json(Path("config/keyword_taxonomy.json"))
    _, components = build_structured_components(taxonomy, "busca2a")
    joined_focus = " ".join(components["focus_terms"]).lower()
    joined_hints = " ".join(components["web_hints"]).lower()

    assert "anti-obesity medication nutrition" in joined_focus
    assert "glp-1 receptor agonist dietary counseling" in joined_focus
    assert "obesity pharmacotherapy nutrition care guideline" in joined_hints
    assert "incretin therapy nutrition care consensus" in joined_hints


def test_busca2b_receives_intervention_oriented_anti_obesity_nutrition_terms() -> None:
    taxonomy = load_json(Path("config/keyword_taxonomy.json"))
    _, components = build_structured_components(taxonomy, "busca2b")
    joined_focus = " ".join(components["focus_terms"]).lower()
    joined_hints = " ".join(components["web_hints"]).lower()

    assert "anti-obesity medication nutrition counseling" in joined_focus
    assert "glp-1 nutrition counseling" in joined_focus
    assert "meal planning during anti-obesity medication" in joined_focus
    assert "lean mass preservation during anti-obesity medication" in joined_focus
    assert "glp-1 receptor agonist nutrition care trial" in joined_hints
    assert "protein intake during anti-obesity medication study" in joined_hints
