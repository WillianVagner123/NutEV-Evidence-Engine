from pathlib import Path

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.settings import load_json


def _rendered_queries(workstream: str, provider: str) -> str:
    taxonomy = load_json(Path("config") / "keyword_taxonomy.json")
    queries = render_queries_for_provider(taxonomy, workstream, provider)
    return "\n".join(queries).lower()


def test_busca2b_pubmed_queries_include_diet_quality_expansion_terms() -> None:
    rendered = _rendered_queries("busca2b", "pubmed")

    assert "dietary fiber" in rendered
    assert "carbohydrate quality" in rendered
    assert "dash eating plan" in rendered
    assert "plant-based protein" in rendered


def test_busca2a_europepmc_queries_include_british_and_pattern_variants() -> None:
    rendered = _rendered_queries("busca2a", "europepmc")

    assert "dietary fibre" in rendered
    assert "low glycaemic index diet" in rendered
    assert "mediterranean eating pattern" in rendered
    assert "portfolio dietary pattern" in rendered
