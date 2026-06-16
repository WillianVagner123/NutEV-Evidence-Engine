from nutev.querypacks.semantic_blocks import semantic_terms


def test_nutrition_care_delivery_terms_are_registered_for_clinical_workstreams():
    busca2a_terms = semantic_terms("busca2a", min_priority=4)
    busca2b_terms = semantic_terms("busca2b", min_priority=4)

    assert "nutrition care delivery" in busca2a_terms
    assert "dietitian-led program" in busca2b_terms
    assert "medical nutrition therapy implementation" in busca2b_terms


def test_nutrition_care_delivery_document_terms_are_registered():
    document_terms = semantic_terms("busca2b", field="document_terms", min_priority=3)

    assert "nutrition care implementation study" in document_terms
    assert "registered dietitian referral pathway" in document_terms
