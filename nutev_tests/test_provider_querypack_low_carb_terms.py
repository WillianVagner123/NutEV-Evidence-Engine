from pathlib import Path

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.settings import load_json


def test_busca2b_pubmed_queries_include_low_carb_and_ketogenic_patterns() -> None:
    taxonomy = load_json(Path("config") / "keyword_taxonomy.json")

    queries = render_queries_for_provider(taxonomy, "busca2b", "pubmed")
    rendered = "\n".join(queries).lower()

    assert "ketogenic diet" in rendered
    assert "low-carbohydrate diet" in rendered
    assert "low carbohydrate diet" in rendered
    assert "carbohydrate-restricted diet" in rendered
    assert "carbohydrate restricted diet" in rendered
