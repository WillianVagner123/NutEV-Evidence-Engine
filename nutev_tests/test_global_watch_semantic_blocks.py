from __future__ import annotations

from nutev.global_watch.semantic_blocks import ckm_watch_terms, dedupe_terms


def test_dedupe_terms_preserves_first_seen_case_insensitive_order() -> None:
    assert dedupe_terms(["CKM risk", "ckm risk", "nutrition", "", " Nutrition "]) == [
        "CKM risk",
        "nutrition",
    ]


def test_ckm_watch_terms_include_nutrition_anchor_and_document_types() -> None:
    terms = {term.lower() for term in ckm_watch_terms()}

    assert "cardiovascular-kidney-metabolic syndrome" in terms
    assert "ckm nutrition" in terms
    assert "medical nutrition therapy" in terms
    assert "clinical decision pathway" in terms
    assert "umbrella review" in terms


def test_ckm_watch_terms_cover_core_nutmev_conditions() -> None:
    terms = {term.lower() for term in ckm_watch_terms()}

    expected_terms = {
        "obesity",
        "cardiometabolic risk",
        "type 2 diabetes",
        "hypertension",
        "dyslipidemia",
        "chronic kidney disease",
        "masld",
        "steatotic liver disease",
    }

    assert expected_terms <= terms
