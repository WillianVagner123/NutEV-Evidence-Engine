from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES


def test_watch_config_expands_cardiometabolic_precision_terms() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["obesity_cardiometabolic"]}

    assert "adiposity-based chronic disease" in terms
    assert "atherosclerotic cardiovascular disease" in terms
    assert "apolipoprotein b" in terms
    assert "triglyceride-rich lipoprotein" in terms


def test_watch_config_expands_diet_pattern_variants() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["diet_patterns"]}

    assert "mediterranean dietary pattern" in terms
    assert "dietary approaches to stop hypertension" in terms
    assert "new nordic diet" in terms
    assert "plant based diet" in terms


def test_watch_config_expands_long_term_adherence_terms() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["implementation_behavior"]}

    assert "long-term adherence" in terms
    assert "diet maintenance" in terms
    assert "weight loss maintenance" in terms
    assert "sustainment" in terms


def test_watch_config_expands_guideline_authority_terms() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["guidelines_consensus"]}

    assert "evidence-based guideline" in terms
    assert "professional society guideline" in terms
