from __future__ import annotations

from nutev.querypacks.semantic_blocks import semantic_terms


def test_food_access_extensions_add_benefit_navigation_terms_to_busca1() -> None:
    rendered = " ".join(semantic_terms("busca1", min_priority=3)).lower()

    assert "health-related social needs" in rendered
    assert "food benefit navigation" in rendered
    assert "snap produce incentive" in rendered
    assert "fresh food pharmacy" in rendered


def test_food_access_extensions_add_document_terms_to_busca2b() -> None:
    rendered = " ".join(
        semantic_terms("busca2b", field="document_terms", min_priority=4)
    ).lower()

    assert "food resource navigation program evaluation" in rendered
    assert "healthy food benefit program evaluation" in rendered
    assert "clinical-community food referral program" in rendered
