from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries


def test_quick_watch_queries_preserve_cardiometabolic_semantic_blocks() -> None:
    queries = build_watch_queries(["obesity_cardiometabolic"], since_days=7, mode="quick")
    rendered = " ".join(str(item["query"]) for item in queries).lower()

    assert "adiposity-based chronic disease" in rendered
    assert "cardiometabolic risk" in rendered
    assert "apolipoprotein b" in rendered
    assert "remnant cholesterol" in rendered
    assert "triglyceride-rich lipoprotein" in rendered
    assert "metabolic dysfunction-associated steatotic liver disease" in rendered
    assert "metabolic dysfunction-associated steatohepatitis" in rendered
    assert "umbrella review" in rendered
