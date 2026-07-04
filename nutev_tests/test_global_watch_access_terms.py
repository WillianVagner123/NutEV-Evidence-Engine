from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries


ACCESS_REFERRAL_TERMS = {
    "food is medicine referral",
    "food as medicine referral",
    "produce prescription referral",
    "nutrition security referral",
    "social prescribing link worker",
    "community resource referral",
    "community health worker-led nutrition",
    "patient navigation",
    "care navigation",
}


def _queries_for(category: str, mode: str = "thesis") -> str:
    rows = build_watch_queries([category], since_days=30, mode=mode)
    return "\n".join(str(row["query"]).lower() for row in rows)


def test_lifestyle_watch_queries_keep_food_access_referral_terms() -> None:
    query_text = _queries_for("lifestyle_medicine")

    missing_terms = [term for term in ACCESS_REFERRAL_TERMS if term not in query_text]

    assert not missing_terms


def test_implementation_watch_queries_keep_food_access_referral_terms() -> None:
    query_text = _queries_for("implementation_behavior")

    missing_terms = [term for term in ACCESS_REFERRAL_TERMS if term not in query_text]

    assert not missing_terms
