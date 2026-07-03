from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES
from nutev.global_watch.watch_query_builder import build_watch_queries


def test_global_watch_obesity_cardiometabolic_includes_ckm_terms() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["obesity_cardiometabolic"]}

    expected_terms = {
        "cardiovascular-kidney-metabolic syndrome",
        "cardiovascular kidney metabolic syndrome",
        "cardiovascular-kidney-metabolic risk",
        "cardiovascular kidney metabolic risk",
        "cardio-kidney-metabolic syndrome",
        "cardio kidney metabolic syndrome",
        "ckm syndrome",
        "ckm health",
        "ckm risk",
        "ckm nutrition",
    }

    assert expected_terms <= terms


def test_quick_watch_queries_surface_ckm_in_cardiometabolic_context() -> None:
    query_text = "\n".join(
        str(item["query"]).lower()
        for item in build_watch_queries(["obesity_cardiometabolic"], 7, "quick")
    )

    assert "cardiometabolic risk" in query_text
    assert "cardiovascular-kidney-metabolic" in query_text
    assert "ckm syndrome" in query_text
