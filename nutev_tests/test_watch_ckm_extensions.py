from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item


def test_quick_mode_obesity_queries_cover_ckm_nutrition_terms() -> None:
    queries = build_watch_queries(["obesity_cardiometabolic"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "cardiovascular-kidney-metabolic nutrition" in rendered
    assert "cardiovascular kidney metabolic nutrition" in rendered
    assert "cardio-kidney-metabolic syndrome" in rendered
    assert "ckm nutrition" in rendered


def test_ckm_nutrition_terms_improve_watch_priority() -> None:
    assert score_watch_item(
        {
            "title": "Cardiovascular-kidney-metabolic nutrition care for obesity and type 2 diabetes",
        }
    ) > score_watch_item({"title": "Obesity and type 2 diabetes care note"})


def test_ckm_acronym_improves_watch_priority() -> None:
    assert score_watch_item(
        {"title": "CKM nutrition care pathway for cardiometabolic risk"}
    ) > score_watch_item({"title": "Cardiometabolic risk care pathway"})
