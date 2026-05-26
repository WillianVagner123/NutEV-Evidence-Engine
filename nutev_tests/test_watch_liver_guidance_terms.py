from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES
from nutev.global_watch.watch_scoring import score_watch_item


def test_guideline_watch_category_includes_liver_guidance_terms() -> None:
    guidance_terms = {term.lower() for term in WATCH_CATEGORIES["guidelines_consensus"]}

    assert "clinical practice update" in guidance_terms
    assert "practice update" in guidance_terms
    assert "hepatology guidance" in guidance_terms
    assert "hepatology practice guidance" in guidance_terms


def test_watch_scoring_rewards_liver_guidance_signals() -> None:
    plain_score = score_watch_item(
        {
            "title": "Nutrition care note",
            "source_provider": "pubmed",
            "download_status": "metadata_only",
        }
    )
    enriched_score = score_watch_item(
        {
            "title": "Clinical practice update for MASLD nutrition care",
            "abstract": "Hepatology guidance for obesity and steatotic liver disease.",
            "source_provider": "pubmed",
            "download_status": "metadata_only",
        }
    )

    assert enriched_score > plain_score + 80
