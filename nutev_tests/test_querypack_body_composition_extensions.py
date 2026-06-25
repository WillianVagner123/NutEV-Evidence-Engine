from __future__ import annotations

import nutev.querypacks  # noqa: F401
from nutev.querypacks.semantic_blocks import (
    semantic_block_names,
    semantic_terms,
)


def test_body_composition_extension_prioritizes_busca2b() -> None:
    assert "body_composition_nutrition" in semantic_block_names("busca2b")


def test_body_composition_extension_adds_nutrition_anchored_terms() -> None:
    terms = {term.lower() for term in semantic_terms("busca2b")}
    assert "sarcopenic obesity" in terms
    assert "protein intake during weight loss" in terms
    assert "lean mass preservation" in terms
