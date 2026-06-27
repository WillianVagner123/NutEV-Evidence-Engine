from __future__ import annotations

from nutev.querypacks.semantic_blocks import semantic_terms


def _terms_for(workstream: str, *, field: str = "terms") -> set[str]:
    return {term.lower() for term in semantic_terms(workstream, field=field, min_priority=4)}


def test_blood_pressure_nutrition_terms_reach_cardiometabolic_workstreams() -> None:
    for workstream in ("busca2a", "busca2b"):
        terms = _terms_for(workstream)
        document_terms = _terms_for(workstream, field="document_terms")

        assert "hypertension nutrition therapy" in terms
        assert "dietary sodium reduction" in terms
        assert "sodium-to-potassium ratio" in terms
        assert "dash diet adherence" in terms
        assert "hypertension nutrition guideline" in document_terms
        assert "blood pressure dietary intervention trial" in document_terms


def test_blood_pressure_nutrition_terms_do_not_expand_busca1() -> None:
    terms = _terms_for("busca1")
    document_terms = _terms_for("busca1", field="document_terms")

    assert "hypertension nutrition therapy" not in terms
    assert "dietary sodium reduction" not in terms
    assert "hypertension nutrition guideline" not in document_terms
