from __future__ import annotations

import nutev.querypacks  # noqa: F401
from nutev.querypacks.semantic_blocks import (
    SEMANTIC_RESEARCH_BLOCKS,
    WORKSTREAM_SEMANTIC_PRIORITIES,
)


def test_adherence_behavior_extensions_add_maintenance_terms() -> None:
    adherence_block = SEMANTIC_RESEARCH_BLOCKS["adherence_persistence"]
    implementation_block = SEMANTIC_RESEARCH_BLOCKS["implementation_science"]

    assert "long-term dietary adherence" in adherence_block["terms"]
    assert "dietary self-regulation" in adherence_block["terms"]
    assert "habit formation intervention" in adherence_block["document_terms"]
    assert "participant engagement" in implementation_block["terms"]


def test_adherence_persistence_priority_is_promoted_for_behavior_workstreams() -> None:
    for workstream in ("busca2b", "artigo3_framework", "a3"):
        first_block, priority = WORKSTREAM_SEMANTIC_PRIORITIES[workstream][0]
        assert first_block == "adherence_persistence"
        assert priority >= 5
