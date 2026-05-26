from pathlib import Path

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.settings import load_json


def test_busca2a_pubmed_queries_include_liver_guidance_terms() -> None:
    taxonomy = load_json(Path("config") / "keyword_taxonomy.json")

    queries = render_queries_for_provider(taxonomy, "busca2a", "pubmed")
    rendered = "\n".join(queries).lower()

    assert "masld" in rendered
    assert "nafld" in rendered
    assert "clinical practice update" in rendered
    assert "hepatology guidance" in rendered
    assert "fatty liver guideline" in rendered
