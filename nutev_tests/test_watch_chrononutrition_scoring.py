from nutev.global_watch.watch_scoring import score_watch_item


def test_chrononutrition_and_meal_timing_signals_improve_priority() -> None:
    assert score_watch_item(
        {
            "title": "Chrononutrition, meal timing, and eating windows for cardiometabolic risk",
        }
    ) > score_watch_item({"title": "Cardiometabolic risk note"})


def test_meal_regularity_and_early_time_restricted_eating_improve_priority() -> None:
    assert score_watch_item(
        {
            "title": "Meal regularity and early time-restricted eating in obesity care",
        }
    ) > score_watch_item({"title": "Obesity care note"})
