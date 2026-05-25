from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES
from nutev.global_watch.watch_scoring import score_watch_item


def test_food_literacy_watch_category_includes_food_security_and_environment_terms() -> None:
    food_terms = {
        term.lower() for term in WATCH_CATEGORIES["food_literacy_culinary_commensality"]
    }

    assert "nutrition security" in food_terms
    assert "food insecurity" in food_terms
    assert "food insecurity screening" in food_terms
    assert "screening for food insecurity" in food_terms
    assert "retail food environment" in food_terms
    assert "healthy food procurement" in food_terms
    assert "menu labeling" in food_terms
    assert "menu labelling" in food_terms


def test_watch_scoring_rewards_food_security_and_environment_signals() -> None:
    plain_score = score_watch_item(
        {
            "title": "Nutrition care note",
            "source_provider": "pubmed",
            "download_status": "metadata_only",
        }
    )
    enriched_score = score_watch_item(
        {
            "title": "Food insecurity screening and retail food environment intervention for obesity nutrition care",
            "abstract": "Healthy food procurement and menu labeling were assessed alongside nutrition security outcomes.",
            "source_provider": "pubmed",
            "download_status": "metadata_only",
        }
    )

    assert enriched_score > plain_score + 45
