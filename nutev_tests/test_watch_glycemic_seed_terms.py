from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries


def test_exhaustive_obesity_watch_queries_cover_glycemic_transition_terms() -> None:
    queries = build_watch_queries(
        ["obesity_cardiometabolic"],
        since_days=30,
        mode="exhaustive",
    )
    rendered = "\n".join(str(item["query"]).lower() for item in queries)

    assert "pre-diabetes" in rendered
    assert "prediabetic state" in rendered
    assert "impaired fasting glucose" in rendered
    assert "impaired glucose tolerance" in rendered
    assert "dysglycemia" in rendered
    assert "dysglycaemia" in rendered
    assert "glucose intolerance" in rendered
    assert "type 2 diabetes remission" in rendered
    assert "remission of type 2 diabetes" in rendered
    assert "glycemic remission" in rendered
    assert "glycaemic remission" in rendered
