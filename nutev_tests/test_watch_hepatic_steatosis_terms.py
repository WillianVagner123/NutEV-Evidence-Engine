from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries


def test_quick_mode_obesity_queries_cover_hepatic_steatosis_variants() -> None:
    queries = build_watch_queries(["obesity_cardiometabolic"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "hepatic steatosis" in rendered
    assert "liver fat" in rendered
