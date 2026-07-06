from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES


def _obesity_cardiometabolic_terms() -> set[str]:
    return {term.lower() for term in WATCH_CATEGORIES["obesity_cardiometabolic"]}


def test_obesity_cardiometabolic_terms_cover_ckm_syndrome_variants() -> None:
    terms = _obesity_cardiometabolic_terms()

    assert "cardiovascular-kidney-metabolic syndrome" in terms
    assert "cardiovascular kidney metabolic syndrome" in terms
    assert "cardio-kidney-metabolic syndrome" in terms
    assert "cardiorenal metabolic syndrome" in terms
    assert "ckm syndrome" in terms
    assert "ckm nutrition" in terms


def test_obesity_cardiometabolic_terms_cover_nutrition_during_obesity_pharmacotherapy() -> None:
    terms = _obesity_cardiometabolic_terms()

    assert "anti-obesity medication nutrition" in terms
    assert "anti-obesity medication dietary counseling" in terms
    assert "obesity pharmacotherapy nutrition care" in terms
    assert "glp-1 nutrition" in terms
    assert "glp-1 dietary counseling" in terms
    assert "incretin therapy nutrition care" in terms


def test_obesity_cardiometabolic_terms_cover_body_composition_preservation() -> None:
    terms = _obesity_cardiometabolic_terms()

    assert "sarcopenic obesity" in terms
    assert "body composition" in terms
    assert "muscle preservation" in terms
    assert "lean mass preservation" in terms
    assert "protein intake" in terms
    assert "dietary protein" in terms
