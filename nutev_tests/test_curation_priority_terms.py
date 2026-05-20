from __future__ import annotations

from nutev.export.curation import _is_prioritized


def test_food_is_medicine_and_produce_prescription_are_prioritized() -> None:
    assert _is_prioritized(
        {
            "title": "Food is medicine and produce prescription program for cardiometabolic risk",
            "relevance_score": 9,
        }
    )


def test_medically_tailored_meals_are_prioritized() -> None:
    assert _is_prioritized(
        {
            "title": "Medically tailored meals for obesity and hypertension",
            "relevance_score": 9,
        }
    )


def test_teaching_kitchen_and_culinary_nutrition_are_prioritized() -> None:
    assert _is_prioritized(
        {
            "title": "Teaching kitchen and culinary nutrition intervention for food literacy",
            "relevance_score": 9,
        }
    )


def test_practice_facilitation_and_quality_improvement_are_prioritized() -> None:
    assert _is_prioritized(
        {
            "title": "Practice facilitation and quality improvement for nutrition care implementation",
            "relevance_score": 9,
        }
    )


def test_priority_terms_still_require_minimum_score() -> None:
    assert not _is_prioritized(
        {
            "title": "Food is medicine and medically tailored meals for cardiometabolic risk",
            "relevance_score": 7,
        }
    )
