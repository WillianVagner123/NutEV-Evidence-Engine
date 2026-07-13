from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item


def test_quick_mode_lifestyle_queries_cover_food_as_medicine_delivery_models() -> None:
    rows = build_watch_queries(["lifestyle_medicine"], 7, "quick")
    rendered = " ".join(str(row["query"]).lower() for row in rows)

    assert "food is medicine" in rendered
    assert "food as medicine" in rendered
    assert "produce prescription" in rendered
    assert "produce rx" in rendered
    assert "fruit and vegetable prescription" in rendered
    assert "healthy food prescription" in rendered
    assert "food prescription program" in rendered
    assert "nutrition prescription" in rendered
    assert "dietary prescription" in rendered
    assert "medically tailored meals" in rendered
    assert "medically tailored groceries" in rendered


def test_quick_mode_implementation_queries_cover_food_as_medicine_label_variants() -> None:
    rows = build_watch_queries(["implementation_behavior"], 7, "quick")
    rendered = " ".join(str(row["query"]).lower() for row in rows)

    assert "produce rx" in rendered
    assert "fruit and vegetable prescription" in rendered
    assert "healthy food prescription" in rendered
    assert "food prescription program" in rendered
    assert "nutrition prescription" in rendered
    assert "prescribed nutrition plan" in rendered


def test_food_as_medicine_and_medically_tailored_meals_improve_priority() -> None:
    assert score_watch_item(
        {
            "title": "Food as medicine produce prescription and medically tailored meals for cardiometabolic risk",
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


def test_nutrition_prescription_improves_priority_when_nutmev_scoped() -> None:
    assert score_watch_item(
        {
            "title": "Nutrition prescription for adults with cardiometabolic risk",
            "abstract": "Dietary prescription in lifestyle medicine nutrition care.",
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
