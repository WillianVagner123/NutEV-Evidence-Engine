from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries


def test_obesity_cardiometabolic_queries_cover_hypertension_precision_terms() -> None:
    queries = build_watch_queries(["obesity_cardiometabolic"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "high blood pressure" in rendered
    assert "elevated blood pressure" in rendered
    assert "blood pressure control" in rendered
    assert "systolic blood pressure" in rendered
    assert "diastolic blood pressure" in rendered
    assert "ambulatory blood pressure" in rendered
    assert "antihypertensive therapy" in rendered
