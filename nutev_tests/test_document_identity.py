from nutev.engine.identity import compute_document_key, merge_article_rows, normalize_doi


def test_compute_document_key_respects_priority_order():
    assert compute_document_key({"doi": "https://doi.org/10.1000/abc"}) == (
        "10.1000/abc",
        "doi",
    )
    assert compute_document_key({"pmid": "12345"}) == ("pmid:12345", "pmid")
    assert compute_document_key({"pmcid": "PMC12345"}) == (
        "pmcid:pmc12345",
        "pmcid",
    )
    assert compute_document_key(
        {"url": "HTTPS://Example.org/path/?x=1"}
    ) == ("https://example.org/path", "url")
    assert compute_document_key({"title": "Same Title", "year": 2024}) == (
        "same title::2024",
        "title_year",
    )


def test_merge_article_rows_prefers_stronger_capture_url_and_longer_abstract():
    merged = merge_article_rows(
        {
            "url": "https://doi.org/10.1000/abc",
            "abstract": "short",
            "source": "pubmed",
        },
        {
            "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC1234567/pdf",
            "abstract": "a much longer abstract",
            "source": "europepmc",
        },
    )

    assert merged["url"] == "https://pmc.ncbi.nlm.nih.gov/articles/PMC1234567/pdf"
    assert merged["abstract"] == "a much longer abstract"
    assert merged["source"] == "pubmed"


def test_normalize_doi_returns_empty_string_for_missing_value():
    assert normalize_doi(None) == ""
