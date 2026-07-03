from __future__ import annotations

import nutev.querypacks  # noqa: F401
from nutev.querypacks import semantic_blocks


def test_diet_quality_indices_extend_cardiometabolic_querypack_terms() -> None:
    terms = semantic_blocks.semantic_terms("busca2b")
    document_terms = semantic_blocks.semantic_terms("busca2b", field="document_terms")
    priorities = semantic_blocks.prioritized_semantic_blocks("busca2b")

    assert "healthy eating index" in terms
    assert "alternate healthy eating index" in terms
    assert "dietary inflammatory index" in terms
    assert "empirical dietary inflammatory pattern" in terms
    assert "diet quality systematic review" in document_terms
    assert "dietary inflammatory index meta-analysis" in document_terms
    assert priorities[0] == {"name": "diet_quality_indices", "priority": 5}


def test_diet_quality_indices_have_moderate_priority_for_busca1() -> None:
    priorities = semantic_blocks.prioritized_semantic_blocks("busca1")

    assert {"name": "diet_quality_indices", "priority": 4} in priorities
