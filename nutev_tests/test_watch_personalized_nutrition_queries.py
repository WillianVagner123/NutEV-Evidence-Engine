from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item


def _render_personalized_queries(mode: str = "quick") -> str:
    queries = build_watch_queries(["personalized_nutrition"], since_days=30, mode=mode)
    assert queries
    return "\n".join(str(item["query"]).lower() for item in queries)


def test_personalized_nutrition_queries_keep_clinical_anchors() -> None:
    rendered = _render_personalized_queries()

    assert "personalized nutrition guideline" in rendered
    assert "personalised nutrition guideline" in rendered
    assert "precision nutrition guideline" in rendered
    assert "tailored dietary advice guideline" in rendered
    assert "personalized nutrition obesity" in rendered
    assert "precision nutrition type 2 diabetes" in rendered
    assert "tailored dietary advice cardiometabolic risk" in rendered


def test_personalized_nutrition_queries_cover_implementation_and_meal_planning() -> None:
    rendered = _render_personalized_queries()

    assert "personalized nutrition implementation" in rendered
    assert "personalised nutrition implementation" in rendered
    assert "precision nutrition implementation" in rendered
    assert "tailored dietary intervention implementation" in rendered
    assert "individualized meal plan obesity" in rendered
    assert "individualised meal plan obesity" in rendered


def test_personalized_nutrition_scoring_prioritizes_clinically_anchored_items() -> None:
    targeted = score_watch_item(
        {
            "title": "Precision nutrition implementation for type 2 diabetes remission",
            "category": "personalized_nutrition",
            "source_provider": "pubmed",
        }
    )
    generic = score_watch_item(
        {
            "title": "Personalized nutrition commentary",
            "category": "personalized_nutrition",
            "source_provider": "pubmed",
        }
    )

    assert targeted > generic
