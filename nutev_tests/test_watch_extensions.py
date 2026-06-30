from __future__ import annotations

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


def test_blood_pressure_nutrition_queries_anchor_sodium_and_potassium_terms() -> None:
    queries = build_watch_queries(
        ["blood_pressure_nutrition"], since_days=30, mode="quick"
    )
    rendered = "\n".join(str(item["query"]).lower() for item in queries)

    assert queries
    assert "dietary sodium hypertension guideline" in rendered
    assert "sodium reduction hypertension" in rendered
    assert "salt substitute hypertension" in rendered
    assert "potassium intake hypertension" in rendered
    assert "dash sodium reduction" in rendered
    assert '"nutrition"' in rendered
    assert '"cardiometabolic"' in rendered
