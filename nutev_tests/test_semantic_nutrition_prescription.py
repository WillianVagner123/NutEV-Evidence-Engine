from __future__ import annotations

from nutev.querypacks import semantic_extensions  # noqa: F401
from nutev.querypacks.semantic_blocks import semantic_terms


def _render_terms(workstream: str, *, field: str = "terms", min_priority: int = 1) -> str:
    return "\n".join(
        semantic_terms(workstream, field=field, min_priority=min_priority)
    ).lower()


def test_busca2_semantic_terms_include_nutrition_prescription_language() -> None:
    terms = _render_terms("busca2b", min_priority=5)

    assert "nutrition prescription" in terms
    assert "dietary prescription" in terms
    assert "nutrition care for diabetes remission" in terms
    assert "dietitian-led remission" in terms


def test_busca2a_document_terms_include_protocol_and_remission_variants() -> None:
    document_terms = _render_terms("busca2a", field="document_terms", min_priority=5)

    assert "nutrition prescription protocol" in document_terms
    assert "dietary prescription guideline" in document_terms
    assert "nutrition care for weight maintenance" in document_terms
    assert "dietitian-led remission protocol" in document_terms


def test_artigo3_framework_inherits_personalized_meal_planning_terms() -> None:
    terms = _render_terms("artigo3_framework", min_priority=5)

    assert "personalized meal planning" in terms
    assert "individualized meal plan" in terms
