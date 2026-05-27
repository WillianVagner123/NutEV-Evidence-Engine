from nutev.querypacks.semantic_blocks import semantic_terms


def test_semantic_blocks_include_healthy_dietary_pattern_variants() -> None:
    busca2a_terms = semantic_terms("busca2a", min_priority=4)
    busca2b_terms = semantic_terms("busca2b", min_priority=5)

    for terms in (busca2a_terms, busca2b_terms):
        assert "healthy eating patterns" in terms
        assert "healthy dietary pattern" in terms
        assert "healthy dietary patterns" in terms
        assert "vegetarian diet" in terms
        assert "vegetarian dietary pattern" in terms
        assert "vegan diet" in terms
        assert "vegan dietary pattern" in terms
        assert "healthy plant-based diet" in terms
