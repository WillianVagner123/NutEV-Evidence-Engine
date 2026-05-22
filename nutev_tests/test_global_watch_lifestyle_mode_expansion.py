from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries


def test_quick_mode_lifestyle_queries_add_culinary_food_literacy_and_dietitian_seeds() -> None:
    queries = build_watch_queries(["lifestyle_medicine"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert len(queries) == 3
    assert "culinary medicine" in rendered
    assert "culinary nutrition" in rendered
    assert "food literacy" in rendered
    assert "food and nutrition literacy" in rendered
    assert "teaching kitchen" in rendered
    assert "teaching kitchens" in rendered
    assert "registered dietitian" in rendered
    assert "registered dietitian nutritionist" in rendered
    assert "dietitian-led" in rendered
    assert "dietitian led" in rendered


def test_exhaustive_mode_lifestyle_queries_add_culinary_and_food_literacy_seeds() -> None:
    queries = build_watch_queries(["lifestyle_medicine"], since_days=7, mode="exhaustive")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert len(queries) == 10
    assert "culinary medicine" in rendered
    assert "culinary nutrition" in rendered
    assert "food literacy" in rendered
    assert "teaching kitchen" in rendered
    assert "teaching kitchens" in rendered


def test_thesis_mode_lifestyle_queries_add_dietitian_delivery_seeds() -> None:
    queries = build_watch_queries(["lifestyle_medicine"], since_days=30, mode="thesis")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert len(queries) == 6
    assert "registered dietitian" in rendered
    assert "registered dietitian nutritionist" in rendered
    assert "dietitian-led" in rendered
    assert "dietitian led" in rendered
