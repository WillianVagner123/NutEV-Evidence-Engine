from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES


def test_lifestyle_watch_category_covers_structured_lifestyle_programs() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["lifestyle_medicine"]}

    assert "structured lifestyle intervention" in terms
    assert "structured lifestyle program" in terms
    assert "structured lifestyle programme" in terms
    assert "group lifestyle balance" in terms


def test_lifestyle_watch_category_covers_diabetes_prevention_and_remission_programs() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["lifestyle_medicine"]}

    assert "national diabetes prevention program" in terms
    assert "diabetes prevention lifestyle intervention" in terms
    assert "prediabetes lifestyle intervention" in terms
    assert "prediabetes prevention program" in terms
    assert "diabetes remission intervention" in terms
    assert "type 2 diabetes remission intervention" in terms


def test_implementation_watch_category_stays_aligned_with_lifestyle_program_terms() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["implementation_behavior"]}

    assert "structured lifestyle intervention" in terms
    assert "diabetes prevention lifestyle intervention" in terms
    assert "prediabetes prevention programme" in terms
    assert "group lifestyle balance" in terms
