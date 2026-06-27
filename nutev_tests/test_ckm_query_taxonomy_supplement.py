from __future__ import annotations

from pathlib import Path

from nutev.querypacks.provider_queries import build_provider_querypack
from nutev.settings import load_json


def test_ckm_supplement_reaches_provider_querypack() -> None:
    taxonomy = load_json(Path("config/keyword_taxonomy.json"))
    querypack = build_provider_querypack(
        taxonomy,
        ["busca2a", "busca2b"],
        {
            "busca2a": ["pubmed", "europepmc", "openalex", "crossref"],
            "busca2b": ["pubmed", "europepmc", "openalex", "crossref"],
        },
    )

    rendered = "\n".join(
        query
        for providers in querypack.values()
        for queries in providers.values()
        for query in queries
    ).lower()

    assert "cardiovascular-kidney-metabolic" in rendered
    assert "ckm syndrome" in rendered
    assert "ckm nutrition" in rendered
