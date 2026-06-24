from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES
from nutev.global_watch.watch_query_builder import build_watch_queries


def _joined_queries(category: str, mode: str) -> str:
    queries = build_watch_queries([category], since_days=7, mode=mode)
    return "\n".join(str(query["query"]).lower() for query in queries)


def test_lifestyle_watch_config_keeps_food_access_terms() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["lifestyle_medicine"]}

    assert "food as medicine" in terms
    assert "produce prescription" in terms
    assert "food pharmacy" in terms
    assert "medically tailored meal" in terms
    assert "nutrition social prescribing" in terms
    assert "food social prescribing" in terms


def test_quick_watch_queries_include_food_as_medicine_access_terms() -> None:
    query_text = _joined_queries("lifestyle_medicine", "quick")

    assert "food as medicine" in query_text
    assert "produce prescription" in query_text
    assert "food pharmacy" in query_text
    assert "nutrition security" in query_text


def test_thesis_implementation_queries_include_community_food_access_terms() -> None:
    query_text = _joined_queries("implementation_behavior", "thesis")

    assert "food as medicine" in query_text
    assert "food insecurity screening" in query_text
    assert "social needs referral" in query_text
    assert "medically tailored meals" in query_text
