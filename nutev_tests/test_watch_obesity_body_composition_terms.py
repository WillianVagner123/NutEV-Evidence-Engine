from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries


def test_quick_mode_obesity_queries_cover_body_composition_nutrition_terms() -> None:
    queries = build_watch_queries(["obesity_cardiometabolic"], since_days=7, mode="quick")
    rendered = "\n".join(str(row["query"]).lower() for row in queries)

    assert "sarcopenic obesity" in rendered
    assert "body composition" in rendered
    assert "muscle preservation" in rendered
    assert "lean mass preservation" in rendered
    assert "protein intake" in rendered
    assert "dietary protein" in rendered
    assert "protein adequacy" in rendered
    assert "high-protein diet" in rendered
