from pathlib import Path

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.settings import load_json


def test_diet_pattern_adherence_instruments_extend_taxonomy_and_pubmed_queries() -> None:
    taxonomy = load_json(Path("config") / "keyword_taxonomy.json")

    busca2b_focus_terms = {
        term.lower()
        for term in taxonomy["workstreams"]["busca2b"].get("focus_terms", [])
    }
    artigo3_hints = {
        term.lower()
        for term in taxonomy["workstreams"]["artigo3_framework"].get("web_query_hints", [])
    }

    assert "mediterranean diet adherence score" in busca2b_focus_terms
    assert "predimed" in busca2b_focus_terms
    assert "medas questionnaire validation" in artigo3_hints

    queries = render_queries_for_provider(taxonomy, "busca2b", "pubmed")
    joined = "\n".join(queries).lower()

    assert '"mediterranean diet adherence score"[title/abstract]' in joined
    assert '"predimed"[title/abstract]' in joined
    assert '"dash adherence score"[title/abstract]' in joined
    assert '"plant-based diet index"[title/abstract]' in joined
