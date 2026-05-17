from nutev.search.pubmed import (
    _clean_doi,
    _clean_pmcid,
    _extract_doi,
    _extract_pmcid,
    _pick_pubmed_url,
)


def test_clean_doi_extracts_doi_from_pii_contaminated_elocationid():
    assert (
        _clean_doi("pii: qdag137. doi: 10.1093/jsxmed/qdag137")
        == "10.1093/jsxmed/qdag137"
    )


def test_clean_doi_accepts_url_and_trailing_punctuation():
    assert (
        _clean_doi("https://doi.org/10.1093/jsxmed/qdag137.")
        == "10.1093/jsxmed/qdag137"
    )
    assert _clean_doi("DOI: 10.1000/ABC-123)") == "10.1000/ABC-123"


def test_extract_doi_prefers_structured_article_id():
    item = {
        "elocationid": "pii: bad. doi: 10.1000/bad",
        "articleids": [
            {"idtype": "pubmed", "value": "123"},
            {"idtype": "doi", "value": "https://doi.org/10.1000/good"},
        ],
    }
    assert _extract_doi(item) == "10.1000/good"


def test_clean_pmcid_normalizes_numeric_and_prefixed_values():
    assert _clean_pmcid("1234567") == "PMC1234567"
    assert _clean_pmcid("PMC 7654321") == "PMC7654321"


def test_extract_pmcid_accepts_pmcid_alias():
    item = {"articleids": [{"idtype": "pmcid", "value": "1234567"}]}

    assert _extract_pmcid(item) == "PMC1234567"


def test_pick_pubmed_url_prefers_pmc_then_doi_then_pubmed():
    assert (
        _pick_pubmed_url("123", "10.1/example", "PMC456")
        == "https://pmc.ncbi.nlm.nih.gov/articles/PMC456/"
    )
    assert (
        _pick_pubmed_url("123", "10.1/example", None)
        == "https://doi.org/10.1/example"
    )
    assert (
        _pick_pubmed_url("123", None, None)
        == "https://pubmed.ncbi.nlm.nih.gov/123/"
    )
