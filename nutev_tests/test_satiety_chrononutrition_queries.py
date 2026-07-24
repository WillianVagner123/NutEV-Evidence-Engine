from __future__ import annotations

from nutev.querypacks.provider_queries import render_queries_for_provider


def test_busca2b_provider_queries_include_satiety_and_chrononutrition_terms() -> None:
    tax = {
        "global": {
            "document_types": {"reviews": ["systematic review"]},
            "implementation_behavior": {"behavioral": ["behavior change"]},
            "diet_patterns": {"core": ["healthy diet"]},
            "nutrition_domains": {"core": ["food literacy"]},
        },
        "clinical": {"obesity": ["obesity"], "diabetes": ["type 2 diabetes"]},
        "outcomes": {"behavioral": ["self efficacy"]},
        "workstreams": {
            "busca2b": {
                "population_terms": ["adult"],
                "condition_terms": ["obesity", "type 2 diabetes"],
                "clinical_keys": ["obesity", "diabetes"],
                "document_type_keys": ["reviews"],
                "priority_outcomes": ["behavioral"],
                "focus_blocks": ["implementation_behavior", "diet_patterns"],
                "web_query_hints": ["implementation study"],
            }
        },
    }

    queries = render_queries_for_provider(tax, "busca2b", "pubmed")
    rendered = "\n".join(queries).lower()

    assert "satiating diet" in rendered
    assert "appetite regulation" in rendered
    assert "meal timing" in rendered
    assert "chrononutrition" in rendered or "chrono-nutrition" in rendered
    assert "type 2 diabetes" in rendered
    assert "obesity" in rendered
