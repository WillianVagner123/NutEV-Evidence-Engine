from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES
from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item


def _queries_as_text(category: str, mode: str = "quick") -> str:
    queries = build_watch_queries([category], since_days=7, mode=mode)
    return "\n".join(str(item["query"]).lower() for item in queries)


def test_global_watch_config_preserves_social_prescribing_access_terms() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["implementation_behavior"]}

    expected_terms = {
        "food pantry referral",
        "social prescribing",
        "social needs referral",
        "closed-loop referral",
        "community food program",
        "food access intervention",
        "nutrition security intervention",
    }

    assert expected_terms <= terms


def test_quick_lifestyle_queries_cover_food_pharmacy_and_grocery_prescription() -> None:
    query_text = _queries_as_text("lifestyle_medicine", mode="quick")

    assert "food pharmacy" in query_text
    assert "grocery prescription" in query_text
    assert "produce prescription" in query_text


def test_social_prescribing_item_keeps_high_watch_priority() -> None:
    item = {
        "title": "Social prescribing program with food pantry referral for obesity and type 2 diabetes",
        "abstract": "Primary care nutrition security intervention with closed-loop referral and dietitian support.",
        "snippet": "Food access intervention for cardiometabolic risk.",
        "evidence_type": "implementation study",
        "category": "implementation_behavior",
        "source_provider": "pubmed",
        "relevance_score": 50,
        "is_new": True,
        "download_status": "metadata_only",
    }

    assert score_watch_item(item) >= 100
