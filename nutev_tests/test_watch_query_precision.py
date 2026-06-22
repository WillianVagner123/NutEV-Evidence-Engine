from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries


def _query_texts(mode: str = "quick") -> list[str]:
    return [str(item["query"]).lower() for item in build_watch_queries([], 7, mode)]


def test_global_watch_keeps_personalized_nutrition_category_visible() -> None:
    queries = _query_texts("quick")

    assert any("personalized nutrition guideline" in query for query in queries)
    assert any("precision nutrition type 2 diabetes" in query for query in queries)
    assert any("tailored dietary intervention obesity" in query for query in queries)


def test_global_watch_keeps_ckm_and_liver_terms_visible() -> None:
    queries = _query_texts("quick")

    assert any("cardiovascular-kidney-metabolic" in query for query in queries)
    assert any("masld" in query and "mash" in query for query in queries)
    assert any("metabolic dysfunction-associated steatotic liver disease" in query for query in queries)


def test_global_watch_keeps_nutrition_anchor_for_broad_lifestyle_terms() -> None:
    queries = _query_texts("quick")
    lifestyle_queries = [query for query in queries if "lifestyle medicine" in query]

    assert lifestyle_queries
    assert any("medical nutrition therapy" in query for query in lifestyle_queries)
