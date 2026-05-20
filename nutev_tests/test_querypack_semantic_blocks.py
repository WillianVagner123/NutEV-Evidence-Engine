from __future__ import annotations

from nutev.querypacks.semantic_blocks import (
    interleaved_semantic_terms,
    semantic_terms,
)


def test_implementation_semantic_block_adds_core_implementation_science_terms() -> None:
    rendered = " ".join(semantic_terms("busca2b", min_priority=4)).lower()

    assert "implementation fidelity" in rendered
    assert "implementation facilitation" in rendered
    assert "implementation support" in rendered
    assert "implementation research" in rendered
    assert "sustainability" in rendered
    assert "dissemination" in rendered
    assert "scale-up" in rendered


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


def test_interleaved_semantic_terms_surface_multiple_priority_blocks_early() -> None:
    rendered = interleaved_semantic_terms("busca2b", min_priority=4)[:5]

    assert rendered[:5] == [
        "implementation science",
        "adherence",
        "systematic review",
        "lifestyle medicine",
        "food literacy",
    ]
