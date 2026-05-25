from pathlib import Path

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.settings import load_json


def test_busca2b_pubmed_queries_include_digital_delivery_terms() -> None:
    taxonomy = load_json(Path("config") / "keyword_taxonomy.json")

    queries = render_queries_for_provider(taxonomy, "busca2b", "pubmed")
    rendered = "\n".join(queries).lower()

    assert "telehealth" in rendered
    assert "telemedicine" in rendered
    assert "digital health" in rendered
    assert "virtual care" in rendered
    assert "remote coaching" in rendered
    assert "digital therapeutics" in rendered
