from __future__ import annotations

from nutev.global_watch.watch_query_builder import build_watch_queries
from nutev.global_watch.watch_scoring import score_watch_item
from nutev.querypacks.provider_queries import render_queries_for_provider


def test_food_literacy_queries_add_labeling_and_security_context() -> None:
    queries = build_watch_queries(
        ["food_literacy_culinary_commensality"],
        since_days=30,
        mode="quick",
    )

    first_query = str(queries[0]["query"])
    assert '"nutrition security"' in first_query
    assert '"nutrition label"' in first_query
    assert '"label reading"' in first_query
    assert '"front-of-pack"' in first_query
    assert '"front-of-pack labeling"' in first_query
    assert '"front-of-pack labelling"' in first_query


def test_food_literacy_thesis_queries_include_social_needs_screening_terms() -> None:
    queries = build_watch_queries(
        ["food_literacy_culinary_commensality"],
        since_days=30,
        mode="thesis",
    )
    rendered = "\n".join(str(query["query"]).lower() for query in queries)

    assert "nutrition security screening" in rendered
    assert "food insecurity screening" in rendered
    assert "social needs referral" in rendered
    assert "social prescribing" in rendered


def test_labeling_and_security_signals_improve_priority() -> None:
    enriched = score_watch_item(
        {
            "title": "Nutrition security and front-of-pack labeling to improve food literacy in obesity care",
        }
    )
    generic = score_watch_item({"title": "Food literacy in obesity care"})

    assert enriched > generic


def test_provider_queries_include_food_environment_implementation_terms() -> None:
    taxonomy = {
        "global": {
            "implementation_behavior": {"core": ["implementation"]},
            "diet_patterns": {"core": ["healthy diet"]},
            "nutrition_domains": {"core": ["nutrition care"]},
            "document_types": {"reviews": ["systematic review"]},
        },
        "clinical": {"glycemia": ["type 2 diabetes"]},
        "outcomes": {"metabolic": ["cardiometabolic"]},
        "workstreams": {
            "busca2b": {
                "population_terms": ["adults with obesity"],
                "condition_terms": ["obesity"],
                "clinical_keys": ["glycemia"],
                "priority_outcomes": ["metabolic"],
                "document_type_keys": ["reviews"],
                "focus_blocks": [],
            },
            "a3": {
                "population_terms": ["adults"],
                "condition_terms": ["obesity"],
                "clinical_keys": [],
                "priority_outcomes": ["metabolic"],
                "document_type_keys": ["reviews"],
                "focus_blocks": [],
            },
        },
    }

    busca2b_queries = "\n".join(render_queries_for_provider(taxonomy, "busca2b", "pubmed")).lower()
    a3_queries = "\n".join(render_queries_for_provider(taxonomy, "a3", "pubmed")).lower()

    assert "food environment intervention" in busca2b_queries
    assert "food procurement policy" in busca2b_queries
    assert "healthy food retail" in a3_queries
    assert "choice architecture" in a3_queries
