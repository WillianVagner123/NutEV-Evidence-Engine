from __future__ import annotations

from nutev.global_watch import watch_config
from nutev.global_watch.watch_query_builder import build_watch_queries


def _render_personalized_queries(mode: str = "quick") -> str:
    queries = build_watch_queries(["personalized_nutrition"], since_days=30, mode=mode)
    return "\n".join(str(item["query"]).lower() for item in queries)


def test_personalized_nutrition_queries_cover_remission_and_weight_maintenance() -> None:
    rendered = _render_personalized_queries()

    assert "personalized nutrition diabetes remission" in rendered
    assert "precision nutrition diabetes remission" in rendered
    assert "tailored dietary intervention diabetes remission" in rendered
    assert "personalized nutrition weight maintenance" in rendered
    assert "precision nutrition weight regain prevention" in rendered


def test_personalized_nutrition_queries_cover_adherence_implementation_terms() -> None:
    rendered = _render_personalized_queries()

    assert "personalized nutrition adherence" in rendered
    assert "precision nutrition adherence" in rendered
    assert "tailored dietary advice adherence" in rendered
    assert "personalized meal planning adherence" in rendered


def test_watch_extensions_add_sustainable_healthy_diet_terms() -> None:
    diet_terms = [term.lower() for term in watch_config.WATCH_CATEGORIES["diet_patterns"]]

    assert "sustainable healthy diets" in diet_terms
    assert "healthy and sustainable diets" in diet_terms
    assert "plant-forward diet" in diet_terms
    assert "plant forward diet" in diet_terms
    assert "flexitarian diet" in diet_terms
    assert "eat-lancet dietary pattern" in diet_terms


def test_watch_extensions_add_sustainable_diet_document_terms_to_guidelines() -> None:
    guideline_terms = [
        term.lower() for term in watch_config.WATCH_CATEGORIES["guidelines_consensus"]
    ]

    assert "sustainable healthy diet guideline" in guideline_terms
    assert "sustainable healthy diets guiding principles" in guideline_terms
    assert "sustainable diets consensus" in guideline_terms
    assert "sustainable diets umbrella review" in guideline_terms
