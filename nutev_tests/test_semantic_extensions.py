from __future__ import annotations

from nutev.querypacks import semantic_blocks


def test_cardiometabolic_nutrition_care_extensions_reach_clinical_workstream() -> None:
    terms = semantic_blocks.semantic_terms("busca2a", min_priority=5)
    document_terms = semantic_blocks.semantic_terms(
        "busca2a",
        field="document_terms",
        min_priority=5,
    )

    assert "cardiometabolic nutrition care" in terms
    assert "nutrition therapy for hypertension" in terms
    assert "medical nutrition therapy for type 2 diabetes" in terms
    assert "nutrition care for steatotic liver disease" in terms
    assert "medical nutrition therapy for type 2 diabetes guideline" in document_terms
    assert "nutrition therapy for cardiometabolic risk systematic review" in document_terms


def test_cardiometabolic_nutrition_care_extensions_reach_intervention_workstream() -> None:
    terms = semantic_blocks.semantic_terms("busca2b", min_priority=5)

    assert "dietitian-led cardiometabolic care" in terms
    assert "nutrition therapy for MASLD" in terms
    assert "diet therapy for dyslipidemia" in terms
