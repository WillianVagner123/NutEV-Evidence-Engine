from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES
from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import BONUS_TERMS, NUTMEV_SCOPE_TERMS, score_watch_item


def _flatten_terms(values: list[object]) -> list[str]:
    terms: list[str] = []
    for value in values:
        if isinstance(value, list):
            terms.extend(str(item) for item in value)
        else:
            terms.append(str(value))
    return terms


def test_personalized_nutrition_category_has_cardio_metabolic_anchors() -> None:
    category_terms = WATCH_CATEGORIES["personalized_nutrition"]
    flattened_terms = _flatten_terms(category_terms)

    assert "precision nutrition type 2 diabetes" in flattened_terms
    assert "tailored dietary advice cardiometabolic risk" in flattened_terms
    assert "tailored dietary intervention obesity" in flattened_terms


def test_personalized_nutrition_quick_watch_query_is_generated() -> None:
    queries = build_watch_queries(["personalized_nutrition"], since_days=30, mode="quick")
    query_text = "\n".join(str(item["query"]) for item in queries)

    assert queries
    assert "precision nutrition type 2 diabetes" in query_text
    assert "tailored dietary advice cardiometabolic risk" in query_text
    assert "obesity" in query_text or "cardiometabolic" in query_text


def test_global_watch_extensions_cover_remission_and_weight_maintenance_terms() -> None:
    queries = build_watch_queries(["obesity_cardiometabolic"], since_days=30, mode="quick")
    query_text = "\n".join(str(item["query"]) for item in queries)
    flattened_terms = _flatten_terms(WATCH_CATEGORIES["obesity_cardiometabolic"])

    assert "nutrition care for diabetes remission" in flattened_terms
    assert "medical nutrition therapy diabetes remission" in query_text
    assert "weight regain prevention nutrition" in query_text
    assert "weight loss maintenance dietary intervention" in query_text


def test_global_watch_extensions_cover_culturally_adapted_nutrition_terms() -> None:
    queries = build_watch_queries(["implementation_behavior"], since_days=30, mode="quick")
    query_text = "\n".join(str(item["query"]) for item in queries)
    flattened_terms = _flatten_terms(WATCH_CATEGORIES["implementation_behavior"])

    assert "culturally adapted nutrition intervention" in flattened_terms
    assert "culturally tailored dietary intervention" in query_text
    assert "culturally appropriate nutrition education" in query_text
    assert "community-based culturally tailored nutrition" in query_text


def test_global_watch_extension_terms_are_scored_inside_nutmev_scope() -> None:
    bonus_terms = dict(BONUS_TERMS)

    assert "nutrition care for diabetes remission" in NUTMEV_SCOPE_TERMS
    assert "culturally adapted nutrition intervention" in NUTMEV_SCOPE_TERMS
    assert bonus_terms["nutrition care for diabetes remission"] >= 20
    assert bonus_terms["culturally adapted nutrition intervention"] >= 18

    score = score_watch_item(
        {
            "title": "Culturally adapted nutrition intervention for type 2 diabetes remission",
            "abstract": "Dietitian-led dietary intervention with weight loss maintenance support.",
            "source_provider": "pubmed",
            "category": "implementation_behavior",
        }
    )

    assert score["is_high_priority"] is True
    assert score["relevance_score"] >= 70
