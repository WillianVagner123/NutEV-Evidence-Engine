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


def test_quick_mode_implementation_queries_cover_adherence_maintenance_terms() -> None:
    queries = build_watch_queries(["implementation_behavior"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "dietary self-monitoring" in rendered
    assert "dietary self-regulation" in rendered
    assert "relapse prevention" in rendered
    assert "lapse management" in rendered
    assert "weight regain prevention" in rendered
    assert "weight regain management" in rendered
    assert "behavioral maintenance" in rendered
    assert "dietary maintenance" in rendered
