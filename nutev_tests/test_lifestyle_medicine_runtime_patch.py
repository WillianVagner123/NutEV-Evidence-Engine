from __future__ import annotations

from pathlib import Path

import usercustomize  # noqa: F401
from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.settings import load_json


def test_busca2a_pubmed_queries_include_lifestyle_medicine_intervention_variants() -> None:
    taxonomy = load_json(Path("config") / "keyword_taxonomy.json")
    queries = [query.lower() for query in render_queries_for_provider(taxonomy, "busca2a", "pubmed")]

    assert '"lifestyle medicine intervention"[title/abstract]' in queries
    assert '"comprehensive lifestyle intervention"[title/abstract]' in queries
    assert '"therapeutic lifestyle intervention"[title/abstract]' in queries


def test_busca2b_pubmed_queries_include_lifestyle_medicine_program_variants() -> None:
    taxonomy = load_json(Path("config") / "keyword_taxonomy.json")
    queries = [query.lower() for query in render_queries_for_provider(taxonomy, "busca2b", "pubmed")]

    assert '"lifestyle medicine intervention"[title/abstract]' in queries
    assert '"lifestyle medicine program"[title/abstract]' in queries
    assert '"lifestyle medicine programme"[title/abstract]' in queries
    assert '"comprehensive lifestyle intervention"[title/abstract]' in queries
    assert '"therapeutic lifestyle intervention"[title/abstract]' in queries
