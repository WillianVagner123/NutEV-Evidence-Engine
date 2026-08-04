from __future__ import annotations

import importlib

from nutev.global_watch.watch_query_builder import build_watch_queries


def _render_personalized_queries(mode: str = "quick") -> str:
    queries = build_watch_queries(["personalized_nutrition"], since_days=30, mode=mode)
    return "\n".join(str(item["query"]).lower() for item in queries)


def _render_obesity_queries(mode: str = "quick") -> str:
    queries = build_watch_queries(["obesity_cardiometabolic"], since_days=30, mode=mode)
    return "\n".join(str(item["query"]).lower() for item in queries)


def _render_diet_pattern_queries(mode: str = "quick") -> str:
    queries = build_watch_queries(["diet_patterns"], since_days=30, mode=mode)
    return "\n".join(str(item["query"]).lower() for item in queries)


def _render_guideline_queries(mode: str = "quick") -> str:
    queries = build_watch_queries(["guidelines_consensus"], since_days=30, mode=mode)
    return "\n".join(str(item["query"]).lower() for item in queries)


def _score_watch_item(item: dict) -> float:
    module = importlib.import_module("nutev.global_watch.watch_scoring")
    return module.score_watch_item(item)


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


def test_obesity_queries_cover_pharmacotherapy_nutrition_terms() -> None:
    rendered = _render_obesity_queries()

    assert "anti-obesity medication nutrition" in rendered
    assert "anti-obesity medication dietary counseling" in rendered
    assert "obesity pharmacotherapy nutrition care" in rendered
    assert "glp-1 receptor agonist nutrition care" in rendered
    assert "incretin therapy dietary counseling" in rendered


def test_pharmacotherapy_nutrition_terms_improve_watch_priority() -> None:
    assert _score_watch_item(
        {
            "title": "GLP-1 receptor agonist nutrition care and dietary counseling for obesity",
        }
    ) > _score_watch_item({"title": "Obesity care note"})


def test_diet_pattern_queries_cover_sustainable_healthy_diets() -> None:
    rendered = _render_diet_pattern_queries()

    assert "sustainable healthy diets" in rendered
    assert "healthy sustainable diets" in rendered
    assert "sustainable dietary patterns" in rendered
    assert "sustainable food-based dietary guidelines" in rendered


def test_guideline_queries_cover_sustainable_dietary_guidelines() -> None:
    rendered = _render_guideline_queries()

    assert "sustainable healthy diets guideline" in rendered
    assert "sustainable food-based dietary guidelines" in rendered
    assert "dietary guidelines sustainability" in rendered


def test_sustainable_healthy_diet_terms_improve_watch_priority() -> None:
    assert _score_watch_item(
        {
            "title": "Sustainable healthy diets guideline for cardiometabolic health",
        }
    ) > _score_watch_item({"title": "Sustainable food systems commentary"})
