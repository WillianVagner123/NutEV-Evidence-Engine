from pathlib import Path

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.settings import load_json


def test_busca2b_pubmed_queries_include_liver_terms_from_tail_conditions():
    taxonomy = load_json(Path("config") / "keyword_taxonomy.json")

    queries = render_queries_for_provider(taxonomy, "busca2b", "pubmed")
    rendered = "\n".join(queries).lower()

    assert "masld" in rendered
    assert "nafld" in rendered
    assert "mash" in rendered
    assert "nash" in rendered
    assert "steatotic liver disease" in rendered
