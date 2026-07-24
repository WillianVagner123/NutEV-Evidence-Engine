from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES
from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item


def test_obesity_cardiometabolic_watch_includes_incretin_nutrition_terms() -> None:
    category_terms = [str(term).lower() for term in WATCH_CATEGORIES["obesity_cardiometabolic"]]

    assert "semaglutide nutrition" in category_terms
    assert "tirzepatide dietary counseling" in category_terms
    assert "lean mass preservation tirzepatide" in category_terms


def test_quick_watch_query_includes_incretin_nutrition_terms() -> None:
    queries = build_watch_queries(["obesity_cardiometabolic"], since_days=30, mode="quick")
    query_text = "\n".join(str(item["query"]).lower() for item in queries)

    assert queries
    assert "semaglutide nutrition" in query_text
    assert "tirzepatide nutrition" in query_text
    assert "cardiometabolic" in query_text or "obesity" in query_text


def test_incretin_nutrition_scores_above_generic_pharmacotherapy_note() -> None:
    targeted = score_watch_item(
        {
            "title": "Tirzepatide nutrition care and lean mass preservation in obesity",
            "abstract": "Dietary counseling supports cardiometabolic risk management.",
            "category": "obesity_cardiometabolic",
            "source_provider": "pubmed",
            "relevance_score": 1,
            "is_new": True,
        }
    )
    generic = score_watch_item(
        {
            "title": "Pharmacotherapy update",
            "abstract": "General medication note without diet or nutrition scope.",
            "category": "obesity_cardiometabolic",
            "source_provider": "pubmed",
            "relevance_score": 1,
        }
    )

    assert targeted > generic
