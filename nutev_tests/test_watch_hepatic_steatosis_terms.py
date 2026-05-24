from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item


def test_obesity_watch_queries_include_hepatic_steatosis_terms_in_quick_mode() -> None:
    queries = build_watch_queries(["obesity_cardiometabolic"], since_days=7, mode="quick")
    rendered = " ".join(str(row["query"]).lower() for row in queries)

    assert "hepatic steatosis" in rendered
    assert "liver steatosis" in rendered
    assert "intrahepatic fat" in rendered
    assert "liver fat content" in rendered


def test_watch_scoring_rewards_hepatic_steatosis_signals() -> None:
    plain_score = score_watch_item(
        {
            "title": "Nutrition and obesity outcomes in adults",
            "source_provider": "pubmed",
            "download_status": "metadata_only",
        }
    )
    enriched_score = score_watch_item(
        {
            "title": "Systematic review of hepatic steatosis and liver fat content in obesity",
            "abstract": "Intrahepatic fat and liver steatosis outcomes were evaluated after dietary interventions.",
            "source_provider": "pubmed",
            "download_status": "metadata_only",
        }
    )

    assert enriched_score > plain_score + 45
