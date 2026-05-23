from __future__ import annotations

import json
from pathlib import Path

from nutev.querypacks.provider_queries import render_queries_for_provider


def _load_keyword_taxonomy() -> dict:
    repo_root = Path(__file__).resolve().parents[2]
    return json.loads(
        (repo_root / "config" / "keyword_taxonomy.json").read_text(encoding="utf-8")
    )


def test_pubmed_queries_include_late_busca2b_outcomes() -> None:
    taxonomy = _load_keyword_taxonomy()

    queries = render_queries_for_provider(taxonomy, "busca2b", "pubmed")
    joined = " ".join(queries).lower()

    assert "postprandial glucose" in joined
    assert "endothelial function" in joined


def test_crossref_queries_include_late_framework_outcomes() -> None:
    taxonomy = _load_keyword_taxonomy()

    queries = render_queries_for_provider(taxonomy, "artigo3_framework", "crossref")
    joined = " ".join(queries).lower()

    assert "healthy eating index" in joined
