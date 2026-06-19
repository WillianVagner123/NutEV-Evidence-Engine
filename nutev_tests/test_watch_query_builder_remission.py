from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries


def _rendered_query(category: str) -> str:
    queries = build_watch_queries([category], since_days=7, mode="quick")
    assert queries
    return " ".join(str(item["query"]).lower() for item in queries)


def test_watch_obesity_context_covers_metabolic_remission_and_weight_maintenance() -> None:
    query = _rendered_query("obesity_cardiometabolic")

    assert "type 2 diabetes remission" in query
    assert "diabetes remission maintenance" in query
    assert "weight regain prevention" in query
    assert "long-term weight loss maintenance" in query


def test_watch_implementation_context_covers_diet_and_lifestyle_remission_terms() -> None:
    query = _rendered_query("implementation_behavior")

    assert "diet-induced diabetes remission" in query
    assert "lifestyle-induced diabetes remission" in query
    assert "remission maintenance" in query
    assert "weight regain management" in query
