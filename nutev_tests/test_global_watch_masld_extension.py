from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES
from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item


def test_masld_nutrition_terms_extend_watch_categories() -> None:
    obesity_terms = WATCH_CATEGORIES["obesity_cardiometabolic"]
    diet_terms = WATCH_CATEGORIES["diet_patterns"]
    guidance_terms = WATCH_CATEGORIES["guidelines_consensus"]

    assert "MASLD dietary intervention" in obesity_terms
    assert "NAFLD lifestyle intervention" in obesity_terms
    assert "MASLD Mediterranean diet" in diet_terms
    assert "steatotic liver disease guideline" in guidance_terms


def test_masld_nutrition_quick_watch_query_is_generated() -> None:
    queries = build_watch_queries(["obesity_cardiometabolic"], since_days=30, mode="quick")
    query_text = "\n".join(str(item["query"]) for item in queries)

    assert queries
    assert "MASLD dietary intervention" in query_text
    assert "NAFLD lifestyle intervention" in query_text
    assert "steatotic liver disease guideline" in query_text


def test_masld_nutrition_guidance_gains_priority() -> None:
    boosted = score_watch_item(
        {
            "title": "MASLD practice guidance for lifestyle intervention and Mediterranean diet nutrition care",
            "abstract": "Clinical practice guideline for adults with obesity and cardiometabolic risk.",
            "source_provider": "pubmed",
            "download_status": "metadata_only",
        }
    )
    baseline = score_watch_item(
        {
            "title": "Liver imaging update for metabolic dysfunction associated steatotic liver disease",
            "abstract": "Technical report for adults.",
            "source_provider": "pubmed",
            "download_status": "metadata_only",
        }
    )

    assert boosted > baseline
