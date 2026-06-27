from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.querypacks.semantic_blocks import prioritized_semantic_blocks, semantic_terms
from nutev.settings import load_json


def test_busca2a_semantic_terms_include_ckm_variants() -> None:
    terms = {term.lower() for term in semantic_terms("busca2a", min_priority=5)}

    assert "cardiovascular-kidney-metabolic syndrome" in terms
    assert "cardiovascular kidney metabolic syndrome" in terms
    assert "ckm syndrome" in terms


def test_busca2a_prioritizes_ckm_precision_block_for_provider_budgets() -> None:
    blocks = prioritized_semantic_blocks("busca2a")

    assert blocks[0] == {"name": "cardiometabolic_precision", "priority": 6}


def test_busca2b_semantic_document_terms_include_ckm_evidence_types() -> None:
    terms = {term.lower() for term in semantic_terms("busca2b", field="document_terms", min_priority=5)}

    assert "presidential advisory" in terms
    assert "clinical decision pathway" in terms


def test_busca2b_pubmed_queries_include_ckm_with_nutrition_or_lifestyle_anchor() -> None:
    taxonomy = load_json("config/keyword_taxonomy.json")

    queries = [
        query.lower()
        for query in render_queries_for_provider(taxonomy, "busca2b", "pubmed")
    ]

    assert any(
        (
            "cardiovascular-kidney-metabolic syndrome" in query
            or "cardiovascular kidney metabolic syndrome" in query
            or "ckm syndrome" in query
        )
        and (
            "nutrition" in query
            or "diet" in query
            or "lifestyle" in query
            or "clinical practice guideline" in query
            or "systematic review" in query
        )
        for query in queries
    )
