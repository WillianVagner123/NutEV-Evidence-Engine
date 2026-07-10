from __future__ import annotations

from pathlib import Path

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.querypacks.semantic_blocks import prioritized_semantic_blocks, semantic_terms
from nutev.settings import load_json


def test_competency_framework_terms_enter_article3_semantic_blocks() -> None:
    terms = {term.lower() for term in semantic_terms("artigo3_framework", min_priority=5)}
    document_terms = {
        term.lower()
        for term in semantic_terms(
            "artigo3_framework",
            field="document_terms",
            min_priority=5,
        )
    }
    priorities = {
        str(block["name"]): int(block["priority"])
        for block in prioritized_semantic_blocks("artigo3_framework")
    }

    assert priorities["professional_competency_frameworks"] == 5
    assert "lifestyle medicine competencies" in terms
    assert "culinary medicine competency framework" in terms
    assert "nutrition competency framework" in document_terms


def test_competency_framework_terms_render_in_article3_provider_queries() -> None:
    keyword_taxonomy = load_json(Path("config/keyword_taxonomy.json"))
    queries = render_queries_for_provider(
        keyword_taxonomy,
        "artigo3_framework",
        "pubmed",
    )
    query_text = "\n".join(queries).lower()

    assert "lifestyle medicine competencies" in query_text
    assert "culinary medicine competency framework" in query_text
    assert "nutrition competency framework" in query_text
