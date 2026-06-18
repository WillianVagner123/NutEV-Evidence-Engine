from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries


def _rendered_query(category: str, mode: str = "quick") -> str:
    queries = build_watch_queries([category], since_days=7, mode=mode)
    assert queries
    return "\n".join(str(row["query"]).lower() for row in queries)


def test_quick_obesity_queries_cover_diabetes_remission_block() -> None:
    rendered = _rendered_query("obesity_cardiometabolic")

    assert "type 2 diabetes remission" in rendered
    assert "diabetes remission" in rendered
    assert "remission of type 2 diabetes" in rendered
    assert "diabetes reversal" in rendered
    assert "glycemic remission" in rendered
    assert "glycaemic remission" in rendered
    assert "metabolic remission" in rendered


def test_quick_implementation_queries_cover_weight_maintenance_block() -> None:
    rendered = _rendered_query("implementation_behavior")

    assert "long-term weight loss maintenance" in rendered
    assert "weight regain prevention" in rendered
    assert "weight regain management" in rendered
    assert "behavioral maintenance" in rendered
    assert "dietary maintenance" in rendered
    assert "relapse prevention" in rendered
    assert "dietary self-monitoring" in rendered
    assert "dietary self-regulation" in rendered


def test_thesis_implementation_queries_cover_maintenance_terms_without_extra_buckets() -> None:
    queries = build_watch_queries(["implementation_behavior"], since_days=30, mode="thesis")
    rendered = "\n".join(str(row["query"]).lower() for row in queries)

    assert len(queries) == 6
    assert "long-term weight loss maintenance" in rendered
    assert "weight regain prevention" in rendered
    assert "dietary self-regulation" in rendered
