from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries


def test_implementation_context_includes_behavior_planning_and_self_regulation_terms() -> None:
    queries = build_watch_queries(["implementation_behavior"], since_days=7, mode="quick")
    rendered = "\n".join(str(item["query"]).lower() for item in queries)

    assert '"action planning"' in rendered
    assert '"coping planning"' in rendered
    assert '"problem solving"' in rendered
    assert '"habit formation"' in rendered
    assert '"dietary self-monitoring"' in rendered
    assert '"dietary self-regulation"' in rendered
    assert '"relapse prevention"' in rendered
    assert '"lapse management"' in rendered
    assert '"readiness to change"' in rendered
