from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries


def test_exhaustive_obesity_watch_queries_cover_glycemic_remission_terms() -> None:
    queries = build_watch_queries(
        ["obesity_cardiometabolic"],
        since_days=30,
        mode="exhaustive",
    )
    rendered = "\n".join(str(item["query"]).lower() for item in queries)

    assert "glycemic remission" in rendered
    assert "glycaemic remission" in rendered
