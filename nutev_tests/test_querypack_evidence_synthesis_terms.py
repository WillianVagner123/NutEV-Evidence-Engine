from pathlib import Path

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.settings import load_json


def test_busca2b_pubmed_queries_include_evidence_synthesis_terms() -> None:
    taxonomy = load_json(Path("config") / "keyword_taxonomy.json")

    queries = render_queries_for_provider(taxonomy, "busca2b", "pubmed")
    rendered = "\n".join(queries).lower()

    assert "systematic review" in rendered
    assert "meta-analysis" in rendered
    assert "network meta-analysis" in rendered
    assert "living systematic review" in rendered
    assert "rapid review" in rendered


def test_busca2a_pubmed_queries_include_guidance_update_variants() -> None:
    taxonomy = load_json(Path("config") / "keyword_taxonomy.json")

    queries = render_queries_for_provider(taxonomy, "busca2a", "pubmed")
    rendered = "\n".join(queries).lower()

    assert "guideline update" in rendered
    assert "living guideline" in rendered
    assert "standards of care" in rendered
    assert "consensus report" in rendered
    assert "clinical guidance" in rendered
