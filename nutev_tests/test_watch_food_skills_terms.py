from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES
from nutev.global_watch.watch_scoring import score_watch_item


def test_food_literacy_watch_category_includes_food_skills_terms() -> None:
    food_terms = {
        term.lower() for term in WATCH_CATEGORIES["food_literacy_culinary_commensality"]
    }

    assert "cooking self-efficacy" in food_terms
    assert "culinary self-efficacy" in food_terms
    assert "food preparation skills" in food_terms
    assert "meal preparation skills" in food_terms
    assert "food shopping skills" in food_terms
    assert "grocery shopping" in food_terms


def test_watch_scoring_rewards_food_skills_signals() -> None:
    plain_score = score_watch_item(
        {
            "title": "Nutrition care note",
            "source_provider": "pubmed",
            "download_status": "metadata_only",
        }
    )
    enriched_score = score_watch_item(
        {
            "title": "Cooking self-efficacy and food shopping skills questionnaire for adults",
            "abstract": (
                "Food preparation skills, meal preparation skills and grocery shopping "
                "were assessed for lifestyle nutrition practice."
            ),
            "source_provider": "pubmed",
            "download_status": "metadata_only",
        }
    )

    assert enriched_score > plain_score + 60