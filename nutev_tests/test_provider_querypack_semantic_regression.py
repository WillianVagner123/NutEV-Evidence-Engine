from __future__ import annotations

import json
from pathlib import Path

from nutev.querypacks.provider_queries import render_queries_for_provider


def _load_keyword_taxonomy() -> dict:
    path = Path(__file__).resolve().parents[1] / "config" / "keyword_taxonomy.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _query_text(keyword_taxonomy: dict, workstream: str, provider: str) -> str:
    queries = render_queries_for_provider(keyword_taxonomy, workstream, provider)
    assert queries, f"expected provider queries for {workstream}/{provider}"
    return "\n".join(queries).lower()


def test_busca2b_provider_queries_preserve_adherence_and_implementation_terms() -> None:
    taxonomy = _load_keyword_taxonomy()

    text = _query_text(taxonomy, "busca2b", "pubmed")

    assert "dietary adherence" in text
    assert "implementation outcomes" in text
    assert "hybrid effectiveness-implementation" in text
    assert "registered dietitian" in text


def test_busca2a_provider_queries_preserve_guideline_and_evidence_synthesis_terms() -> None:
    taxonomy = _load_keyword_taxonomy()

    text = _query_text(taxonomy, "busca2a", "europepmc")

    assert "clinical practice guideline" in text
    assert "consensus guidance" in text
    assert "standards of care" in text
    assert "umbrella review" in text
