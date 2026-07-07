from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item


def test_thesis_mode_implementation_behavior_uses_semantic_seed_groups() -> None:
    queries = build_watch_queries(
        categories=["implementation_behavior"],
        since_days=30,
        mode="thesis",
    )

    assert len(queries) == 6
    assert any(
        '"digital health"' in query["query"] and '"telehealth"' in query["query"]
        for query in queries
    )
    assert any(
        '"implementation science"' in query["query"]
        and '"implementation outcomes"' in query["query"]
        for query in queries
    )


def test_quick_mode_includes_group_based_lifestyle_care_terms() -> None:
    queries = build_watch_queries(
        categories=["implementation_behavior"],
        since_days=30,
        mode="quick",
    )

    assert any(
        '"group nutrition counseling"' in query["query"]
        and '"shared medical appointments"' in query["query"]
        for query in queries
    )


def test_score_watch_item_rewards_digital_implementation_signals() -> None:
    base_item = {
        "title": "Lifestyle nutrition support for obesity care",
        "abstract": "Program evaluation for dietary counseling.",
        "source_provider": "pubmed",
    }
    digital_item = {
        **base_item,
        "title": "Digital health and telehealth implementation for lifestyle nutrition support in obesity care",
        "abstract": "Implementation outcomes framework with remote coaching and digital therapeutics.",
    }

    assert score_watch_item(digital_item) > score_watch_item(base_item)


def test_score_watch_item_rewards_group_based_lifestyle_care_signals() -> None:
    base_item = {
        "title": "Lifestyle nutrition support for obesity care",
        "abstract": "Program evaluation for dietary counseling.",
        "source_provider": "pubmed",
    }
    group_care_item = {
        **base_item,
        "title": "Group nutrition counseling and shared medical appointments for obesity care",
        "abstract": "A lifestyle medicine group visit implementation for type 2 diabetes prevention.",
    }

    assert score_watch_item(group_care_item) > score_watch_item(base_item)
