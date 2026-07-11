from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries


def test_frameworks_instruments_queries_keep_nutev_context_terms() -> None:
    queries = build_watch_queries(["frameworks_instruments"], since_days=7, mode="quick")
    rendered = " ".join(str(item["query"]).lower() for item in queries)

    assert "framework" in rendered
    assert "questionnaire" in rendered
    assert "survey instrument" in rendered
    assert "psychometric validation" in rendered
    assert "scale development" in rendered
    assert "lifestyle medicine competencies" in rendered
    assert "food literacy" in rendered
    assert "culinary medicine" in rendered
    assert "culinary nutrition" in rendered
    assert "commensality" in rendered
