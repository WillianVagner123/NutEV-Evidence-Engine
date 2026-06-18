from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES
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


def test_implementation_watch_category_covers_behavioral_maintenance_terms() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["implementation_behavior"]}

    assert "behavioral maintenance" in terms
    assert "dietary maintenance" in terms
    assert "relapse prevention" in terms
    assert "lapse management" in terms
