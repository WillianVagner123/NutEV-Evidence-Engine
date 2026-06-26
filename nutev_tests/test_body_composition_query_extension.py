from __future__ import annotations

import json
from pathlib import Path

from nutev.querypacks import apply_body_composition_extensions
from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.querypacks.semantic_blocks import (
    SEMANTIC_RESEARCH_BLOCKS,
    WORKSTREAM_SEMANTIC_PRIORITIES,
)


def test_body_composition_extension_is_prioritized_for_busca2b() -> None:
    apply_body_composition_extensions()

    block = SEMANTIC_RESEARCH_BLOCKS["body_composition_preservation"]

    assert "sarcopenic obesity" in block["terms"]
    assert "dietary protein intervention trial" in block["document_terms"]
    assert ("body_composition_preservation", 4) in WORKSTREAM_SEMANTIC_PRIORITIES[
        "busca2b"
    ]


def test_body_composition_terms_render_in_provider_queries() -> None:
    apply_body_composition_extensions()
    taxonomy = json.loads(Path("config/keyword_taxonomy.json").read_text(encoding="utf-8"))

    queries = render_queries_for_provider(taxonomy, "busca2b", "pubmed")
    rendered = "\n".join(queries).lower()

    assert "sarcopenic obesity" in rendered
    assert "dietary protein intervention trial" in rendered
