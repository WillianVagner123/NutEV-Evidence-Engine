from __future__ import annotations

from pathlib import Path

from nutev.querypacks.builders import build_structured_components
from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.settings import load_json


def _taxonomy() -> dict:
    return load_json(Path("config/keyword_taxonomy.json"))


def test_ckm_terms_are_loaded_for_cardiometabolic_workstreams() -> None:
    taxonomy = _taxonomy()

    _, busca2a_components = build_structured_components(taxonomy, "busca2a")
    _, busca2b_components = build_structured_components(taxonomy, "busca2b")

    assert "cardiovascular-kidney-metabolic syndrome" in busca2a_components["condition_terms"]
    assert "ckm syndrome guideline" in busca2a_components["web_hints"]
    assert "cardiovascular-kidney-metabolic risk" in busca2b_components["condition_terms"]
    assert "ckm syndrome lifestyle intervention" in busca2b_components["web_hints"]


def test_ckm_terms_reach_provider_queries() -> None:
    taxonomy = _taxonomy()

    busca2a_pubmed = "\n".join(render_queries_for_provider(taxonomy, "busca2a", "pubmed")).lower()
    busca2b_europepmc = "\n".join(render_queries_for_provider(taxonomy, "busca2b", "europepmc")).lower()

    assert '"ckm syndrome"[title/abstract]' in busca2a_pubmed
    assert 'title_abs:"cardiovascular-kidney-metabolic risk"' in busca2b_europepmc
