from __future__ import annotations

from nutev.export.curation import _is_prioritized


def test_is_prioritized_for_food_incentive_and_voucher_programs() -> None:
    row = {
        "relevance_score": 9,
        "title": "Healthy food incentive and produce voucher program in adults",
        "abstract": "Community implementation with food access support.",
    }

    assert _is_prioritized(row) is True


def test_is_prioritized_for_medically_tailored_pantry_programs() -> None:
    row = {
        "relevance_score": 9,
        "title": "Medically tailored pantry and food package delivery for adults",
        "summary": "Operational evaluation of a nutrition support program.",
    }

    assert _is_prioritized(row) is True
