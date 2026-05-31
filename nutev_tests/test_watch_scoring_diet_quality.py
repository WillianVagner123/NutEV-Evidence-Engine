from __future__ import annotations

from nutev.global_watch.watch_scoring import score_watch_item


def test_diet_quality_index_signals_improve_priority() -> None:
    assert score_watch_item(
        {
            "title": "Healthy Eating Index and Alternative Healthy Eating Index for cardiometabolic risk",
        }
    ) > score_watch_item({"title": "Diet quality for cardiometabolic risk"})


def test_named_plant_based_diet_indexes_improve_priority() -> None:
    assert score_watch_item(
        {
            "title": "Healthful plant-based diet index and diet quality score in type 2 diabetes",
        }
    ) > score_watch_item({"title": "Plant-based diet in type 2 diabetes"})
