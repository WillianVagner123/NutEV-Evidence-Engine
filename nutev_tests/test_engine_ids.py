from nutev.engine.ids import make_document_id


def test_document_id_stable_for_doi():
    a = make_document_id({"doi": "10.1000/ABC"})
    b = make_document_id({"doi": "https://doi.org/10.1000/abc"})
    assert a == b


def test_document_id_stable_for_url():
    a = make_document_id({"final_url": "https://Example.com/paper/"})
    b = make_document_id({"final_url": "https://example.com/paper"})
    assert a == b


def test_document_id_uses_pmid_before_url():
    a = make_document_id({"pmid": "123456", "url": "https://example.com/a"})
    b = make_document_id({"pmid": 123456, "url": "https://example.com/b"})
    assert a == b


def test_document_id_uses_pmcid_before_url():
    a = make_document_id({"pmcid": "PMC123456", "url": "https://example.com/a"})
    b = make_document_id({"pmcid": "123456", "url": "https://example.com/b"})
    assert a == b


def test_document_id_title_year_fallback_is_provider_agnostic():
    a = make_document_id({"title": "Shared Title", "year": 2024, "source_provider": "pubmed"})
    b = make_document_id({"title": "Shared Title", "year": 2024, "source_provider": "openalex"})
    assert a == b
