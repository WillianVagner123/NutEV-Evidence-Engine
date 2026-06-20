import json
from pathlib import Path

from nutev.querypacks.builders import build_queries
from nutev.querypacks.provider_queries import render_queries_for_provider


def _load_taxonomy() -> dict:
    return json.loads(
        (Path(__file__).resolve().parents[2] / "config" / "keyword_taxonomy.json").read_text(
            encoding="utf-8"
        )
    )


def test_pubmed_queries_include_diet_quality_index_terms_for_cardiometabolic_workstreams():
    taxonomy = _load_taxonomy()

    busca2a_queries = render_queries_for_provider(taxonomy, "busca2a", "pubmed")
    busca2b_queries = render_queries_for_provider(taxonomy, "busca2b", "pubmed")
    rendered = "\n".join(busca2a_queries + busca2b_queries).lower()

    assert "diet quality index" in rendered
    assert "healthy eating index" in rendered
    assert "alternate healthy eating index" in rendered
    assert "dietary inflammatory index" in rendered
    assert "empirical dietary inflammatory pattern" in rendered


def test_busca2b_structured_queries_anchor_diet_quality_to_cardiometabolic_scope():
    taxonomy = _load_taxonomy()

    queries = build_queries(taxonomy, "busca2b")
    rendered = "\n".join(queries).lower()

    assert "diet quality index" in rendered
    assert "healthy eating index" in rendered
    assert "dietary inflammatory index" in rendered
    assert "cardiometabolic" in rendered
    assert "type 2 diabetes" in rendered
    assert "dyslipidemia" in rendered
