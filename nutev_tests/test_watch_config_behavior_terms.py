from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries


def test_quick_mode_implementation_queries_cover_planning_and_stage_of_change_terms() -> None:
    queries = build_watch_queries(["implementation_behavior"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "action planning" in rendered
    assert "coping planning" in rendered
    assert "self-regulation" in rendered
    assert "self regulation" in rendered
    assert "readiness to change" in rendered
    assert "stage of change" in rendered
    assert "stages of change" in rendered
    assert "transtheoretical model" in rendered


def test_exhaustive_implementation_queries_cover_diet_adherence_quality_terms() -> None:
    queries = build_watch_queries(
        ["implementation_behavior"],
        since_days=7,
        mode="exhaustive",
    )
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "diet adherence" in rendered
    assert "dietary adherence intervention" in rendered
    assert "dietary pattern adherence" in rendered
    assert "mediterranean diet adherence" in rendered
    assert "dash diet adherence" in rendered
    assert "healthy eating behavior change" in rendered
    assert "diet quality intervention" in rendered
