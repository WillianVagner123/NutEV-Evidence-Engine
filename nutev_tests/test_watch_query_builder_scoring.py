from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item


def test_implementation_behavior_queries_include_nutrition_care_and_dietitian_terms():
    queries = build_watch_queries(["implementation_behavior"], since_days=30, mode="quick")
    query_text = " ".join(item["query"] for item in queries).lower()

    assert "nutrition care pathway" in query_text
    assert "registered dietitian-led intervention" in query_text or "dietitian-delivered intervention" in query_text


def test_watch_scoring_prioritizes_nutrition_care_implementation_hits():
    baseline = {
        "title": "Lifestyle counseling program",
        "abstract": "Behavior support for adults with obesity.",
        "snippet": "",
        "evidence_type": "study",
        "category": "implementation_behavior",
        "relevance_score": 0,
    }
    enriched = {
        **baseline,
        "title": "Registered dietitian-led intervention using a nutrition care pathway",
        "abstract": "Implementation study of a nutrition care process model in obesity care.",
    }

    assert score_watch_item(enriched) > score_watch_item(baseline)


def test_intensive_behavioral_nutrition_terms_enter_quick_queries_and_score():
    queries = build_watch_queries(["implementation_behavior"], since_days=30, mode="quick")
    query_text = " ".join(item["query"] for item in queries).lower()

    assert "intensive behavioral therapy obesity nutrition" in query_text
    assert "shared medical appointment nutrition" in query_text
    assert "dietitian-led behavioral weight management" in query_text

    baseline = {
        "title": "Behavioral weight management program for obesity",
        "abstract": "Adults received lifestyle support in primary care.",
        "snippet": "",
        "evidence_type": "study",
        "category": "implementation_behavior",
        "relevance_score": 0,
    }
    enriched = {
        **baseline,
        "title": "Dietitian-led behavioral weight management in obesity shared medical appointments",
        "abstract": "Intensive behavioral therapy obesity nutrition program in primary care.",
    }

    assert score_watch_item(enriched) > score_watch_item(baseline)
