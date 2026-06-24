from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries


def _quick_query(category: str) -> str:
    queries = build_watch_queries([category], since_days=7, mode="quick")
    return "\n".join(str(item["query"]).lower() for item in queries)


def test_quick_obesity_watch_queries_include_diabetes_remission_terms() -> None:
    rendered = _quick_query("obesity_cardiometabolic")

    assert "type 2 diabetes remission" in rendered
    assert "remission of type 2 diabetes" in rendered
    assert "diabetes reversal" in rendered
    assert "glycemic remission" in rendered


def test_quick_implementation_watch_queries_include_weight_maintenance_terms() -> None:
    rendered = _quick_query("implementation_behavior")

    assert "diabetes remission maintenance" in rendered
    assert "weight regain prevention" in rendered
    assert "weight loss maintenance intervention" in rendered
    assert "nutrition care for diabetes remission" in rendered


def test_quick_lifestyle_watch_queries_include_remission_care_delivery_terms() -> None:
    rendered = _quick_query("lifestyle_medicine")

    assert "diabetes remission intervention" in rendered
    assert "dietitian-led remission" in rendered
    assert "nutrition care for diabetes remission" in rendered
