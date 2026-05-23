from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item


def test_obesity_watch_queries_include_lipid_risk_terms_in_quick_mode() -> None:
    queries = build_watch_queries(["obesity_cardiometabolic"], since_days=7, mode="quick")

    joined_queries = " ".join(str(query["query"]) for query in queries).lower()

    assert "atherogenic dyslipidemia" in joined_queries
    assert "hypertriglyceridemia" in joined_queries
    assert "remnant cholesterol" in joined_queries
    assert "triglyceride-rich lipoprotein" in joined_queries


def test_watch_scoring_rewards_lipid_risk_signals() -> None:
    plain_score = score_watch_item(
        {
            "title": "Diet and obesity outcomes in adults",
            "abstract": "",
            "source_provider": "pubmed",
            "download_status": "metadata_only",
        }
    )
    enriched_score = score_watch_item(
        {
            "title": "Systematic review of atherogenic dyslipidemia and remnant cholesterol in obesity",
            "abstract": "Triglyceride-rich lipoprotein burden and apolipoprotein B were evaluated.",
            "source_provider": "pubmed",
            "download_status": "metadata_only",
        }
    )

    assert enriched_score > plain_score + 40
