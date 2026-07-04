from __future__ import annotations

import importlib

from nutev.global_watch.watch_query_builder import build_watch_queries


def _render_personalized_queries(mode: str = "quick") -> str:
    queries = build_watch_queries(["personalized_nutrition"], since_days=30, mode=mode)
    return "\n".join(str(item["query"]).lower() for item in queries)


def _render_obesity_queries(mode: str = "quick") -> str:
    queries = build_watch_queries(["obesity_cardiometabolic"], since_days=30, mode=mode)
    return "\n".join(str(item["query"]).lower() for item in queries)


def _render_implementation_queries(mode: str = "quick") -> str:
    queries = build_watch_queries(["implementation_behavior"], since_days=30, mode=mode)
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
    assert "nutrition care for diabetes remission" in rendered
    assert "medical nutrition therapy weight maintenance" in rendered
    assert "dietitian-led weight maintenance" in rendered


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


def test_obesity_queries_cover_metabolic_maintenance_terms() -> None:
    rendered = _render_obesity_queries()

    assert "type 2 diabetes remission" in rendered
    assert "remission of type 2 diabetes" in rendered
    assert "weight regain prevention" in rendered
    assert "long-term weight loss maintenance" in rendered
    assert "dietary self-regulation" in rendered


def test_implementation_queries_cover_maintenance_and_self_regulation_terms() -> None:
    rendered = _render_implementation_queries()

    assert "relapse prevention" in rendered
    assert "lapse management" in rendered
    assert "behavioral maintenance" in rendered
    assert "dietary self-monitoring" in rendered
    assert "dietary self-regulation" in rendered


def test_guideline_queries_cover_metabolic_maintenance_document_terms() -> None:
    rendered = _render_guideline_queries()

    assert "diabetes remission guideline" in rendered
    assert "diabetes remission consensus report" in rendered
    assert "weight loss maintenance systematic review" in rendered
    assert "weight regain prevention trial" in rendered


def test_pharmacotherapy_nutrition_terms_improve_watch_priority() -> None:
    assert _score_watch_item(
        {
            "title": "GLP-1 receptor agonist nutrition care and dietary counseling for obesity",
        }
    ) > _score_watch_item({"title": "Obesity care note"})


def test_metabolic_maintenance_terms_improve_watch_priority() -> None:
    assert _score_watch_item(
        {
            "title": "Dietary self-monitoring for long-term weight loss maintenance and diabetes remission",
        }
    ) > _score_watch_item({"title": "Weight management note"})
