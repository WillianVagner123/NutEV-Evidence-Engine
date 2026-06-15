from __future__ import annotations

from pathlib import Path

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.querypacks.semantic_blocks import (
    prioritized_semantic_blocks,
    semantic_terms,
)
from nutev.settings import load_json


def test_choice_architecture_block_is_prioritized_for_intervention_workstreams() -> None:
    busca2b_blocks = prioritized_semantic_blocks("busca2b")
    artigo3_blocks = prioritized_semantic_blocks("artigo3_framework")

    assert {"name": "choice_architecture_nudging", "priority": 4} in busca2b_blocks
    assert {"name": "choice_architecture_nudging", "priority": 4} in artigo3_blocks


def test_choice_architecture_terms_enter_high_priority_semantic_terms() -> None:
    terms = " ".join(semantic_terms("busca2b", min_priority=4)).lower()

    assert "choice architecture" in terms
    assert "behavioral economics" in terms
    assert "point-of-choice prompt" in terms
    assert "retail food environment intervention" in terms


def test_choice_architecture_terms_render_in_provider_queries() -> None:
    keyword_taxonomy = load_json(Path("config/keyword_taxonomy.json"))
    queries = render_queries_for_provider(keyword_taxonomy, "busca2b", "pubmed")
    joined_queries = "\n".join(queries).lower()

    assert '"choice architecture"[title/abstract]' in joined_queries
    assert '"behavioral economics"[title/abstract]' in joined_queries
    assert '"nudge intervention"[title/abstract]' in joined_queries
