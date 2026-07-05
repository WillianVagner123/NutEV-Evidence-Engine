from __future__ import annotations

from nutev.export.curation import _is_prioritized
from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item
from nutev.querypacks.semantic_blocks import semantic_terms


def test_build_watch_queries_includes_hybrid_implementation_terms() -> None:
    queries = build_watch_queries(["implementation_behavior"], since_days=7, mode="quick")
    query_texts = [str(item["query"]) for item in queries]

    assert any("hybrid type 1" in query.lower() for query in query_texts)
    assert any("implementation framework" in query.lower() for query in query_texts)
    assert any("normalization process theory" in query.lower() for query in query_texts)


def test_build_watch_queries_include_behavior_change_framework_terms() -> None:
    queries = build_watch_queries(["implementation_behavior"], since_days=7, mode="thesis")
    query_texts = [str(item["query"]).lower() for item in queries]

    assert any("behavior change wheel" in query for query in query_texts)
    assert any("com-b" in query for query in query_texts)
    assert any("intervention mapping" in query for query in query_texts)


def test_build_watch_queries_include_self_efficacy_variants() -> None:
    quick_queries = build_watch_queries(["implementation_behavior"], since_days=7, mode="quick")
    thesis_queries = build_watch_queries(["implementation_behavior"], since_days=30, mode="thesis")
    rendered = " ".join(
        [str(item["query"]).lower() for item in quick_queries]
        + [str(item["query"]).lower() for item in thesis_queries]
    )

    assert "self-efficacy" in rendered
    assert "self efficacy" in rendered


def test_semantic_extensions_cover_nutrition_navigation_terms() -> None:
    food_terms = {term.lower() for term in semantic_terms("food_literacy_agency")}
    implementation_terms = {term.lower() for term in semantic_terms("implementation_science")}

    assert "food self-management" in food_terms
    assert "dietary self management" in food_terms
    assert "food resource navigator" in food_terms
    assert "community health worker nutrition counseling" in implementation_terms
    assert "social prescribing nutrition" in implementation_terms


def test_score_watch_item_rewards_hybrid_framework_markers() -> None:
    baseline = score_watch_item(
        {
            "title": "Implementation study for obesity care",
            "abstract": "Nutrition program delivery in adults.",
            "snippet": "",
            "evidence_type": "study",
            "category": "implementation_behavior",
            "relevance_score": 50,
            "download_status": "metadata_only",
            "source_provider": "pubmed",
        }
    )
    hybrid = score_watch_item(
        {
            "title": "Hybrid type 2 implementation study using CFIR and normalization process theory",
            "abstract": "Lifestyle medicine nutrition intervention with implementation framework outcomes.",
            "snippet": "",
            "evidence_type": "study",
            "category": "implementation_behavior",
            "relevance_score": 50,
            "download_status": "metadata_only",
            "source_provider": "pubmed",
        }
    )

    assert hybrid > baseline


def test_score_watch_item_rewards_behavior_change_framework_markers() -> None:
    baseline = score_watch_item(
        {
            "title": "Behavior change support for obesity nutrition care",
            "abstract": "Adult implementation support in lifestyle medicine.",
            "snippet": "",
            "evidence_type": "study",
            "category": "implementation_behavior",
            "relevance_score": 50,
            "download_status": "metadata_only",
            "source_provider": "pubmed",
        }
    )
    enriched = score_watch_item(
        {
            "title": (
                "COM-B and behavior change wheel intervention mapping for obesity "
                "nutrition implementation"
            ),
            "abstract": "Motivational interviewing strategy for adherence and implementation outcomes.",
            "snippet": "",
            "evidence_type": "study",
            "category": "implementation_behavior",
            "relevance_score": 50,
            "download_status": "metadata_only",
            "source_provider": "pubmed",
        }
    )

    assert enriched > baseline


def test_curated_priority_flags_hybrid_implementation_documents() -> None:
    prioritized = _is_prioritized(
        {
            "title": "Hybrid type 1 implementation framework for lifestyle medicine nutrition care",
            "abstract": "Uses RE-AIM and CFIR to evaluate adherence and implementation outcomes.",
            "summary": "",
            "snippet": "",
            "evidence_type": "study",
            "domains": "implementation_behavior",
            "outcomes": "adherence",
            "diet_patterns": "",
            "clinical_conditions": "obesity",
            "main_terms": "",
            "journal": "Implementation Science",
            "source_institution": "",
            "relevance_score": 8,
        }
    )

    assert prioritized is True


def test_curated_priority_flags_behavior_change_framework_documents() -> None:
    prioritized = _is_prioritized(
        {
            "title": "Behavior change wheel and COM-B framework for obesity nutrition implementation",
            "abstract": (
                "Intervention mapping and motivational interviewing were used to improve "
                "dietary adherence in adults with cardiometabolic risk."
            ),
            "summary": "",
            "snippet": "",
            "evidence_type": "study",
            "domains": "implementation_behavior",
            "outcomes": "adherence",
            "diet_patterns": "",
            "clinical_conditions": "obesity; cardiometabolic risk",
            "main_terms": "",
            "journal": "BMC Health Services Research",
            "source_institution": "",
            "relevance_score": 8,
        }
    )

    assert prioritized is True
