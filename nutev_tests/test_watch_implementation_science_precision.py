from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item


def test_implementation_queries_add_readiness_and_sustainment_signals() -> None:
    queries = build_watch_queries(["implementation_behavior"], since_days=30, mode="quick")
    rendered = " ".join(str(item["query"]).lower() for item in queries)

    assert "appropriateness" in rendered
    assert "implementation climate" in rendered
    assert "organizational readiness" in rendered
    assert "readiness for implementation" in rendered
    assert "penetration" in rendered
    assert "sustainment" in rendered


def test_readiness_and_sustainment_signals_improve_priority() -> None:
    enriched = score_watch_item(
        {
            "title": (
                "Organizational readiness, implementation climate, appropriateness, "
                "and sustainment in lifestyle nutrition implementation"
            ),
            "abstract": "Readiness for implementation and penetration improved.",
        }
    )
    generic = score_watch_item({"title": "Lifestyle nutrition implementation note"})

    assert enriched > generic
