from nutev.search.pubmed import _clean_doi, _extract_doi


def test_clean_doi_extracts_doi_from_pii_contaminated_elocationid():
    assert _clean_doi("pii: qdag137. doi: 10.1093/jsxmed/qdag137") == "10.1093/jsxmed/qdag137"


def test_extract_doi_prefers_structured_article_id():
    item = {
        "elocationid": "pii: bad. doi: 10.1000/bad",
        "articleids": [
            {"idtype": "pubmed", "value": "123"},
            {"idtype": "doi", "value": "10.1000/good"},
        ],
    }
    assert _extract_doi(item) == "10.1000/good"
