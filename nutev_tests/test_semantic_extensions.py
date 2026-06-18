from __future__ import annotations

from nutev.querypacks import semantic_blocks


def test_semantic_extensions_add_habit_maintenance_terms_to_adherence_block() -> None:
    block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS["adherence_persistence"]

    assert "habit formation" in block["terms"]
    assert "dietary self-regulation" in block["terms"]
    assert "implementation intentions" in block["terms"]
    assert "relapse prevention intervention" in block["document_terms"]


def test_semantic_extensions_add_habit_maintenance_terms_to_implementation_block() -> None:
    block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS["implementation_science"]

    assert "habit-based dietary intervention" in block["terms"]
    assert "maintenance of behavior change" in block["terms"]
    assert "implementation intentions intervention" in block["document_terms"]
