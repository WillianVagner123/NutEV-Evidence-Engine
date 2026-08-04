from nutev.querypacks.semantic_blocks import semantic_terms


def test_busca2_cardiometabolic_semantics_include_ckm_terms():
    for workstream in ("busca2a", "busca2b"):
        terms = {term.lower() for term in semantic_terms(workstream, min_priority=5)}

        assert "cardiovascular-kidney-metabolic syndrome" in terms
        assert "cardiovascular kidney metabolic risk" in terms
        assert "ckm syndrome" in terms
        assert "cardiorenal metabolic syndrome" in terms


def test_busca2_cardiometabolic_document_terms_include_ckm_guidance():
    for workstream in ("busca2a", "busca2b"):
        document_terms = {
            term.lower()
            for term in semantic_terms(workstream, field="document_terms", min_priority=5)
        }

        assert "cardiovascular-kidney-metabolic syndrome guideline" in document_terms
        assert "cardiovascular kidney metabolic syndrome statement" in document_terms
        assert "ckm syndrome guideline" in document_terms
        assert "ckm syndrome statement" in document_terms
