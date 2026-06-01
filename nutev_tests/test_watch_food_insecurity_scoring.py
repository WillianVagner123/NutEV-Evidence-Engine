from __future__ import annotations

from nutev.global_watch.watch_scoring import score_watch_item


def test_food_insecurity_and_social_needs_improve_priority() -> None:
    prioritized = score_watch_item(
        {
            "title": "Food insecurity and health-related social needs in cardiometabolic nutrition care",
        }
    )
    generic = score_watch_item({"title": "Cardiometabolic nutrition care note"})

    assert prioritized > generic


def test_food_pharmacy_signal_improves_priority() -> None:
    prioritized = score_watch_item(
        {"title": "Fresh food pharmacy intervention for diabetes and hypertension care"}
    )
    generic = score_watch_item({"title": "Diabetes and hypertension care note"})

    assert prioritized > generic
