from __future__ import annotations

from nutev.querypacks.semantic_blocks import semantic_terms


def _lowered_terms(workstream: str, *, field: str = "terms") -> set[str]:
    return {term.lower() for term in semantic_terms(workstream, field=field, min_priority=3)}


def test_adherence_maintenance_behavior_terms_reach_busca2b_querypack() -> None:
    busca2b_terms = _lowered_terms("busca2b")

    assert "dietary self-monitoring intervention" in busca2b_terms
    assert "implementation intentions" in busca2b_terms
    assert "habit-based intervention" in busca2b_terms
    assert "dietary adherence support" in busca2b_terms


def test_adherence_maintenance_document_terms_reach_busca2b_querypack() -> None:
    busca2b_document_terms = _lowered_terms("busca2b", field="document_terms")

    assert "relapse prevention intervention" in busca2b_document_terms
    assert "behavioral maintenance intervention" in busca2b_document_terms
    assert "implementation intentions intervention" in busca2b_document_terms
