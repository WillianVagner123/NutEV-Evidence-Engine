from __future__ import annotations

import json
from pathlib import Path

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.querypacks.semantic_blocks import semantic_terms


def _load_taxonomy() -> dict:
    return json.loads(Path("config/keyword_taxonomy.json").read_text(encoding="utf-8"))


def test_group_care_terms_are_prioritized_for_busca2b_provider_queries() -> None:
    taxonomy = _load_taxonomy()

    terms = {term.lower() for term in semantic_terms("busca2b", min_priority=5)}
    assert "diabetes self-management education and support" in terms
    assert "group-based lifestyle intervention" in terms

    pubmed_queries = render_queries_for_provider(taxonomy, "busca2b", "pubmed")
    joined_queries = "\n".join(pubmed_queries).lower()

    assert "diabetes self-management education and support" in joined_queries
    assert "group-based lifestyle intervention" in joined_queries
    assert "obesity" in joined_queries or "type 2 diabetes" in joined_queries
