from __future__ import annotations

from nutev.export.curation import _is_prioritized
from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item


def test_build_watch_queries_includes_hybrid_implementation_terms() -> None:
    queries = build_watch_queries(["implementation_behavior"], since_days=7, mode="quick")
    query_texts = [str(item["query"]) for item in queries]

    assert any("hybrid type 1" in query.lower() for query in query_texts)
    assert any("implementation framework" in query.lower() for query in query_texts)
    assert any("normalization process theory" in query.lower() for query in query_texts)


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
