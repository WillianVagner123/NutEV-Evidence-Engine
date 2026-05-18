from pathlib import Path

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.settings import load_json


def test_busca2b_pubmed_queries_include_new_implementation_science_terms():
    taxonomy = load_json(Path("config") / "keyword_taxonomy.json")

    queries = render_queries_for_provider(taxonomy, "busca2b", "pubmed")
    rendered = "\n".join(queries).lower()

    assert "implementation research" in rendered
    assert "implementation strategy" in rendered
    assert "implementation outcomes" in rendered
    assert "implementation fidelity" in rendered
