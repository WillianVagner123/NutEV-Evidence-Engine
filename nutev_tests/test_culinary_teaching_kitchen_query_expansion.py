from __future__ import annotations

from pathlib import Path

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.settings import load_json


def _provider_query_text(workstream: str, provider: str) -> str:
    taxonomy = load_json(Path("config/keyword_taxonomy.json"))
    queries = render_queries_for_provider(taxonomy, workstream, provider)
    return "\n".join(queries).lower()


def test_busca2b_queries_include_culinary_intervention_terms() -> None:
    query_text = _provider_query_text("busca2b", "pubmed")

    assert "culinary medicine intervention" in query_text
    assert "teaching kitchen evaluation" in query_text
    assert "cooking skills intervention" in query_text


def test_a3_queries_include_culinary_instrument_terms() -> None:
    query_text = _provider_query_text("a3", "europepmc")

    assert "cooking self-efficacy" in query_text
    assert "food resource management" in query_text
    assert "food label literacy" in query_text


def test_busca1_queries_include_culinary_grey_literature_terms() -> None:
    query_text = _provider_query_text("busca1", "openalex")

    assert "culinary medicine program" in query_text
    assert "teaching kitchen program report" in query_text
    assert "experiential nutrition education report" in query_text
