"""Tests for rich thematic detection + evidence snippets."""
from __future__ import annotations

from pathlib import Path

from nutev.analysis.thematic import (
    classify_doc_type,
    detect_themes,
    evidence_rows,
    evidence_weight,
    extract_nutrition_values,
    load_taxonomy,
    thematic_fields,
)

CONFIG = Path(__file__).resolve().parents[1] / "config"
TAX = load_taxonomy(CONFIG)

_TEXT = (
    "These food-based dietary guidelines recommend the Mediterranean diet and DASH diet. "
    "Sleep quality and stress management matter, and physical activity is encouraged. "
    "The guideline discusses mental health and depression, cooking skills and meal planning, "
    "reading nutrition labels, and avoiding ultra-processed foods (NOVA classification). "
    "It notes adherence, affordability and cost, and cultural context. "
    "Aim for 45-65% carbohydrate, 25 g fiber and under 2000 mg sodium; ensure potassium and calcium."
)


def test_taxonomy_loads():
    assert "families" in TAX and "diet_patterns" in TAX["families"]


def test_detect_themes_finds_families_with_snippets():
    themes = detect_themes(_TEXT, TAX)
    assert "diet_patterns" in themes and "mediterranean" in themes["diet_patterns"]
    assert "lm_pillars" in themes and "sleep" in themes["lm_pillars"]
    assert "neuro_mental" in themes and "depression" in themes["neuro_mental"]
    assert "eating_competencies" in themes and "culinary" in themes["eating_competencies"]
    assert "processing" in themes and "ultra_processed" in themes["processing"]
    # Evidence snippet is a verbatim window that contains the matched term.
    snip = themes["diet_patterns"]["mediterranean"]["snippets"][0]
    assert "mediterranean diet" in snip.lower()


def test_classify_doc_type_and_weight():
    assert classify_doc_type(_TEXT, TAX) == "guideline"
    assert evidence_weight("guideline", TAX) == 5
    assert evidence_weight("other", TAX) == 1
    assert classify_doc_type("A randomized clinical trial of diet.", TAX) == "trial"


def test_extract_nutrition_values():
    n = extract_nutrition_values(_TEXT, TAX)
    assert "45-65%" in n["macros_pct"]
    assert "25g" in n["fiber_g"]
    assert "2000" in n["sodium"]
    assert "potassium" in n["micronutrients"] and "calcium" in n["micronutrients"]


def test_thematic_fields_flat_and_nested():
    fields = thematic_fields({"extracted_text": _TEXT}, TAX)
    assert fields["doc_type"] == "guideline" and fields["evidence_weight"] == 5
    assert "mediterranean" in fields["diet_patterns"] and "dash" in fields["diet_patterns"]
    assert fields["n_themes"] >= 8
    assert "diet_patterns:mediterranean" in fields["themes_present"]
    assert isinstance(fields["themes"], dict)


def test_evidence_rows_carry_reference():
    fields = thematic_fields({"extracted_text": _TEXT, "name": "Brazil FBDG"}, TAX)
    record = {"name": "Brazil FBDG", "reference": "MoH. FBDG. Brazil. 2014.", **fields}
    rows = evidence_rows(record)
    assert rows and all(r["reference"] == "MoH. FBDG. Brazil. 2014." for r in rows)
    med = [r for r in rows if r["subtheme"] == "mediterranean"][0]
    assert "mediterranean" in med["evidence_snippet"].lower()
    assert med["family"] == "diet_patterns"


def test_empty_text_is_safe():
    fields = thematic_fields({}, TAX)
    assert fields["n_themes"] == 0 and fields["themes"] == {}
    assert evidence_rows({"themes": {}}) == []
