from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item


def test_obesity_cardiometabolic_watch_queries_include_ckm_terms() -> None:
    queries = build_watch_queries(["obesity_cardiometabolic"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "cardiovascular-kidney-metabolic syndrome" in rendered
    assert "cardiovascular kidney metabolic risk" in rendered
    assert "ckm syndrome" in rendered


def test_ckm_statement_keeps_nutmev_scope_priority() -> None:
    score = score_watch_item(
        {
            "title": "Cardiovascular-kidney-metabolic syndrome scientific statement for nutrition and lifestyle care",
            "source_provider": "pubmed",
            "is_new": True,
        }
    )

    assert score >= 70
