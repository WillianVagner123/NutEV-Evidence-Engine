from __future__ import annotations

from nutev.global_watch.watch_scoring import score_watch_item


def test_glp1_nutrition_care_scores_more_than_generic_obesity_note() -> None:
    assert score_watch_item(
        {
            "title": "GLP-1 receptor agonist nutrition care for obesity pharmacotherapy",
        }
    ) > score_watch_item({"title": "Obesity pharmacotherapy note"})


def test_aom_dietary_counseling_keeps_nutmev_scope_signal() -> None:
    assert score_watch_item(
        {
            "title": "Anti-obesity medication dietary counseling for cardiometabolic care",
        }
    ) > score_watch_item({"title": "Anti-obesity medication update"})
