from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries


def _rendered_category_query(category: str) -> str:
    queries = build_watch_queries([category], since_days=7, mode="quick")
    assert queries
    return " ".join(str(item["query"]).lower() for item in queries)


def test_quick_mode_obesity_queries_cover_remission_maintenance_terms() -> None:
    rendered = _rendered_category_query("obesity_cardiometabolic")

    assert "glycemic remission" in rendered
    assert "glycaemic remission" in rendered
    assert "diabetes remission maintenance" in rendered
    assert "type 2 diabetes remission maintenance" in rendered
    assert "weight regain prevention intervention" in rendered


def test_quick_mode_lifestyle_queries_cover_remission_program_terms() -> None:
    rendered = _rendered_category_query("lifestyle_medicine")

    assert "type 2 diabetes remission program" in rendered
    assert "type 2 diabetes remission programme" in rendered
    assert "remission maintenance" in rendered
    assert "total diet replacement program" in rendered
    assert "very low energy diet program" in rendered


def test_guidelines_queries_cover_remission_guidance_terms() -> None:
    rendered = _rendered_category_query("guidelines_consensus")

    assert "diabetes remission guideline" in rendered
    assert "type 2 diabetes remission guideline" in rendered
    assert "diabetes remission consensus report" in rendered
    assert "weight loss maintenance guideline" in rendered


def test_implementation_queries_cover_remission_and_diet_replacement_terms() -> None:
    rendered = _rendered_category_query("implementation_behavior")

    assert "diabetes remission maintenance" in rendered
    assert "type 2 diabetes remission maintenance" in rendered
    assert "total diet replacement intervention" in rendered
    assert "very low energy diet intervention" in rendered
