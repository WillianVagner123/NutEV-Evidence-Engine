from __future__ import annotations

from nutev.querypacks.semantic_blocks import semantic_terms


def _lowered_terms(workstream: str, *, field: str = "terms") -> set[str]:
    return {term.lower() for term in semantic_terms(workstream, field=field, min_priority=3)}


def test_adherence_maintenance_terms_reach_behavioral_workstreams() -> None:
    busca2b_terms = _lowered_terms("busca2b")
    framework_terms = _lowered_terms("artigo3_framework")

    assert "dietary relapse prevention" in busca2b_terms
    assert "weight maintenance intervention" in busca2b_terms
    assert "maintenance of behavior change" in framework_terms
    assert "dietary self-management support" in framework_terms


def test_adherence_maintenance_document_terms_reach_clinical_queries() -> None:
    busca2a_doc_terms = _lowered_terms("busca2a", field="document_terms")
    busca2b_doc_terms = _lowered_terms("busca2b", field="document_terms")

    assert "weight maintenance intervention trial" in busca2a_doc_terms
    assert "habit formation intervention" in busca2b_doc_terms
    assert "long-term dietary adherence intervention" in busca2b_doc_terms
