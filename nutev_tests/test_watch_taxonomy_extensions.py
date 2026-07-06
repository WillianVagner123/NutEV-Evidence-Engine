from __future__ import annotations

from nutev.global_watch import watch_scoring
from nutev.global_watch.watch_query_builder import build_watch_queries


def test_referral_integration_terms_extend_quick_queries_and_scoring() -> None:
    queries = build_watch_queries(
        categories=["implementation_behavior"],
        since_days=7,
        mode="quick",
    )
    query_text = "\n".join(str(query["query"]).lower() for query in queries)

    assert "clinical-community linkage nutrition" in query_text
    assert "food is medicine referral pathway" in query_text

    score = watch_scoring.score_watch_item(
        {
            "title": "Clinical-community linkage nutrition referral in primary care",
            "abstract": "Implementation of food is medicine referral pathway for cardiometabolic risk.",
            "source_provider": "pubmed",
            "download_status": "metadata_only",
        }
    )

    assert score >= 40
    assert watch_scoring.NUTMEV_SCOPE_TERMS.count("clinical-community linkage nutrition") == 1
    assert watch_scoring.BONUS_TERMS.count(("food is medicine referral pathway", 20)) == 1
