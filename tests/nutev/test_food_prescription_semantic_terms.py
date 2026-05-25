import json
from pathlib import Path

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.querypacks.semantic_blocks import semantic_terms


_CONFIG_ROOT = Path(__file__).resolve().parents[2] / "config"


def _load_taxonomy() -> dict:
    return json.loads(
        (_CONFIG_ROOT / "keyword_taxonomy.json").read_text(encoding="utf-8")
    )


def test_semantic_terms_include_voucher_and_incentive_variants_for_busca2b() -> None:
    terms = semantic_terms("busca2b", min_priority=5)

    assert "healthy food incentive" in terms
    assert "produce voucher" in terms
    assert "fruit and vegetable voucher" in terms
    assert "medically tailored pantry" in terms
    assert "medically tailored food package" in terms


def test_pubmed_provider_queries_surface_new_food_prescription_variants() -> None:
    taxonomy = _load_taxonomy()

    queries = render_queries_for_provider(taxonomy, "busca2b", "pubmed")

    assert any(
        token in query
        for query in queries
        for token in (
            "healthy food incentive",
            "produce voucher",
            "fruit and vegetable voucher",
            "medically tailored pantry",
            "medically tailored food package",
        )
    )
