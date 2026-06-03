from nutev.global_watch.watch_config import WATCH_CATEGORIES
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


def test_watch_config_includes_iberoamerican_nutrition_and_cardiometabolic_terms():
    guidelines = {term.lower() for term in WATCH_CATEGORIES["guidelines_consensus"]}
    cardiometabolic = {term.lower() for term in WATCH_CATEGORIES["obesity_cardiometabolic"]}
    implementation = {term.lower() for term in WATCH_CATEGORIES["implementation_behavior"]}
    food_literacy = {term.lower() for term in WATCH_CATEGORIES["food_literacy_culinary_commensality"]}

    assert "guia alimentar" in guidelines
    assert "diretrizes alimentares" in guidelines
    assert "risco cardiometabolico" in cardiometabolic
    assert "diabetes tipo 2" in cardiometabolic
    assert "barreiras e facilitadores" in implementation
    assert "literacia alimentar" in food_literacy
