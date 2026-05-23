from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item


def test_build_watch_queries_include_diabetes_standards_and_implementation_design_terms_in_thesis_mode():
    queries = build_watch_queries([], 30, "thesis")
    query_texts = [str(item["query"]).lower() for item in queries]

    assert any("standards of medical care in diabetes" in query for query in query_texts)
    assert any(
        "implementation trial" in query
        or "hybrid type 2" in query
        or "quality improvement study" in query
        for query in query_texts
    )


def test_watch_scoring_boosts_diabetes_standards_and_implementation_trials():
    generic_guideline = {
        "title": "Guideline for nutrition care in type 2 diabetes",
        "abstract": "Adult obesity and type 2 diabetes nutrition care.",
        "snippet": "",
        "evidence_type": "guideline",
        "category": "guidelines_consensus",
        "relevance_score": 50,
        "source_provider": "pubmed",
        "download_status": "metadata_only",
        "is_new": False,
    }
    diabetes_standards = {
        **generic_guideline,
        "title": "Standards of Medical Care in Diabetes for obesity and nutrition therapy",
    }

    generic_implementation = {
        "title": "Implementation program for adult obesity and food as medicine",
        "abstract": "Primary care dietary support with food as medicine delivery.",
        "snippet": "",
        "evidence_type": "study",
        "category": "implementation_behavior",
        "relevance_score": 50,
        "source_provider": "pubmed",
        "download_status": "metadata_only",
        "is_new": False,
    }
    stronger_implementation = {
        **generic_implementation,
        "title": (
            "Hybrid type 2 implementation trial and quality improvement study "
            "for a food as medicine intervention in adult obesity"
        ),
    }

    assert score_watch_item(diabetes_standards) > score_watch_item(generic_guideline)
    assert score_watch_item(stronger_implementation) > score_watch_item(generic_implementation)
