from __future__ import annotations

from nutev.global_watch.watch_scoring import score_watch_item


def test_practical_guideline_signal_improves_priority() -> None:
    assert score_watch_item(
        {
            "title": "Practical guideline for cardiometabolic nutrition care",
        }
    ) > score_watch_item({"title": "Cardiometabolic nutrition care note"})


def test_evidence_based_recommendation_signal_improves_priority() -> None:
    assert score_watch_item(
        {
            "title": "Evidence-based recommendation for obesity nutrition care",
        }
    ) > score_watch_item({"title": "Obesity nutrition care note"})


def test_behavioral_and_dietary_maintenance_signals_improve_priority() -> None:
    assert score_watch_item(
        {
            "title": "Behavioral maintenance intervention and dietary maintenance intervention for weight regain prevention",
        }
    ) > score_watch_item({"title": "Weight regain prevention note"})
