from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries


def test_exhaustive_watch_queries_include_dietician_and_nutritionist_led_variants() -> None:
    queries = build_watch_queries(["implementation_behavior"], since_days=30, mode="exhaustive")
    rendered = "\n".join(str(item["query"]).lower() for item in queries)

    assert "registered dietician" in rendered
    assert "dietician-led intervention" in rendered
    assert "nutritionist-led intervention" in rendered


def test_exhaustive_lifestyle_queries_include_provider_spelling_variants() -> None:
    queries = build_watch_queries(["lifestyle_medicine"], since_days=30, mode="exhaustive")
    rendered = "\n".join(str(item["query"]).lower() for item in queries)

    assert "registered dietician" in rendered
    assert "dietician-led" in rendered
    assert "nutritionist-led" in rendered
