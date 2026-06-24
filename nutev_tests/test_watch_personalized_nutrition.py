from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries


def _render_queries(mode: str = "quick") -> str:
    queries = build_watch_queries(["personalized_nutrition"], since_days=7, mode=mode)
    assert queries
    return "\n".join(str(row["query"]).lower() for row in queries)


def test_personalized_nutrition_watch_queries_include_cardiometabolic_anchors() -> None:
    rendered = _render_queries("quick")

    assert '"personalized nutrition obesity"' in rendered
    assert '"precision nutrition type 2 diabetes"' in rendered
    assert '"tailored dietary advice cardiometabolic risk"' in rendered
    assert '"individualized dietary intervention type 2 diabetes"' in rendered
    assert '"nutrition"' in rendered
    assert '"obesity"' in rendered
    assert '"cardiometabolic"' in rendered


def test_quick_mode_personalized_nutrition_covers_guideline_implementation_and_core_blocks() -> None:
    rendered = _render_queries("quick")

    assert "personalized nutrition guideline" in rendered
    assert "personalised nutrition guideline" in rendered
    assert "precision nutrition guideline" in rendered
    assert "tailored dietary advice guideline" in rendered
    assert "personalized nutrition implementation" in rendered
    assert "precision nutrition implementation" in rendered
    assert "tailored dietary intervention implementation" in rendered
    assert "personalized nutrition cardiometabolic risk" in rendered
    assert "tailored dietary intervention obesity" in rendered
    assert "personalized nutrition" in rendered
    assert "precision nutrition" in rendered
    assert "diet personalization" in rendered


def test_default_quick_mode_includes_personalized_nutrition_category() -> None:
    queries = build_watch_queries(None, since_days=7, mode="quick")
    categories = {str(row["category"]) for row in queries}

    assert "personalized_nutrition" in categories
