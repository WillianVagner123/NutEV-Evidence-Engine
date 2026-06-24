from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries


def test_obesity_watch_queries_cover_hepatometabolic_liver_variants() -> None:
    queries = build_watch_queries(["obesity_cardiometabolic"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "hepatic steatosis" in rendered
    assert "metabolic-associated fatty liver disease" in rendered
    assert "metabolic associated fatty liver disease" in rendered
    assert "metabolic-associated steatotic liver disease" in rendered
    assert "metabolic associated steatotic liver disease" in rendered


def test_diet_pattern_context_retains_masld_retrieval_context() -> None:
    queries = build_watch_queries(["diet_patterns"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "masld" in rendered
    assert "mash" in rendered
    assert "hepatic steatosis" in rendered
