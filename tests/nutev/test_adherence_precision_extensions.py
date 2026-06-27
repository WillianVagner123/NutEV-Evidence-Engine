from nutev.querypacks.semantic_blocks import semantic_terms


def test_adherence_precision_terms_enter_busca2b_semantic_blocks() -> None:
    terms = semantic_terms("busca2b", min_priority=5)
    document_terms = semantic_terms(
        "busca2b",
        field="document_terms",
        min_priority=5,
    )

    assert "dietary action planning" in terms
    assert "habit strength" in terms
    assert "self-monitoring of food intake" in terms
    assert "dietary self-monitoring intervention" in document_terms
    assert "habit formation intervention" in document_terms
