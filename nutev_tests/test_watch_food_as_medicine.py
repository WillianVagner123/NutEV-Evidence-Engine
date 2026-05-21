from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item


def test_quick_mode_lifestyle_queries_cover_food_as_medicine_delivery_models() -> None:
    rows = build_watch_queries(["lifestyle_medicine"], 7, "quick")
    rendered = " ".join(str(row["query"]).lower() for row in rows)

    assert "food is medicine" in rendered
    assert "produce prescription" in rendered
    assert "medically tailored meals" in rendered
    assert "medically tailored groceries" in rendered


def test_food_as_medicine_and_medically_tailored_meals_improve_priority() -> None:
    assert score_watch_item(
        {
            "title": "Food is medicine produce prescription and medically tailored meals for cardiometabolic risk",
            "relevance_score": 1,
            "is_new": True,
        }
    ) > score_watch_item(
        {
            "title": "Cardiometabolic risk note",
            "relevance_score": 1,
            "is_new": True,
        }
    )
