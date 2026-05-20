from __future__ import annotations

from nutev.querypacks.semantic_blocks import semantic_terms


def test_implementation_semantic_block_adds_core_implementation_science_terms() -> None:
    rendered = " ".join(semantic_terms("busca2b", min_priority=4)).lower()

    assert "implementation fidelity" in rendered
    assert "implementation facilitation" in rendered
    assert "implementation support" in rendered
    assert "implementation research" in rendered
    assert "sustainability" in rendered
    assert "dissemination" in rendered
    assert "scale-up" in rendered
    assert "food is medicine" in rendered
    assert "produce prescription" in rendered
    assert "medically tailored meals" in rendered


def test_implementation_semantic_block_adds_document_level_terms() -> None:
    rendered = " ".join(
        semantic_terms("busca2b", field="document_terms", min_priority=4)
    ).lower()

    assert "implementation evaluation" in rendered
    assert "dissemination study" in rendered
    assert "hybrid type 2" in rendered


def test_lifestyle_nutrition_semantic_block_adds_pattern_and_lifestyle_terms() -> None:
    rendered = " ".join(semantic_terms("busca2b", min_priority=4)).lower()

    assert "therapeutic lifestyle changes" in rendered
    assert "mediterranean dietary pattern" in rendered
    assert "dietary approaches to stop hypertension" in rendered
    assert "planetary health diet" in rendered


def test_food_literacy_semantic_block_adds_culinary_training_terms() -> None:
    rendered = " ".join(semantic_terms("artigo3_framework", min_priority=5)).lower()

    assert "culinary nutrition" in rendered
    assert "teaching kitchen" in rendered
    assert "teaching kitchens" in rendered
    assert "home cooking" in rendered
    assert "meal preparation" in rendered
    assert "cooking confidence" in rendered
    assert "nutrition education" in rendered
