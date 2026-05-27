from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item


def test_framework_watch_queries_include_psychometric_validation_terms_in_quick_mode() -> None:
    queries = build_watch_queries(["frameworks_instruments"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "content validity" in rendered
    assert "construct validity" in rendered
    assert "test-retest reliability" in rendered
    assert "cross-cultural adaptation" in rendered


def test_framework_watch_scoring_rewards_psychometric_validation_signals() -> None:
    plain_score = score_watch_item(
        {
            "title": "Food literacy framework for nutrition behavior",
            "source_provider": "pubmed",
            "download_status": "metadata_only",
        }
    )
    enriched_score = score_watch_item(
        {
            "title": "Cross-cultural adaptation and psychometric validation of a food literacy questionnaire",
            "abstract": "Content validity, construct validity, internal consistency, and test-retest reliability were evaluated.",
            "source_provider": "pubmed",
            "download_status": "metadata_only",
        }
    )

    assert enriched_score > plain_score + 55
