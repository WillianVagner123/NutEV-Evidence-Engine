from __future__ import annotations

from nutev.search.preprints import _normalize_preprint, search_preprints

EXPECTED_KEYS = {
    "source",
    "source_provider",
    "title",
    "abstract",
    "snippet",
    "doi",
    "pmid",
    "pmcid",
    "url",
    "journal",
    "year",
    "publication_date",
    "article_type",
    "authors",
    "metadata_status",
    "query",
    "provider_query",
    "oa_pdf_url",
    "is_open_access",
}


def _sample_item() -> dict:
    return {
        "id": "PPR123456",
        "source": "PPR",
        "title": "A preprint on dietary patterns and metabolic health",
        "authorString": "Smith J, Doe A.",
        "journalTitle": "medRxiv",
        "pubYear": "2023",
        "doi": "10.1101/2023.01.01.23000001",
        "pmid": "",
        "pmcid": "",
        "firstPublicationDate": "2023-01-15",
        "abstractText": "We investigated dietary patterns.",
    }


def test_normalize_preprint_maps_fields():
    row = _normalize_preprint(_sample_item(), "dietary patterns")

    assert row["source"] == "preprints"
    assert row["source_provider"] == "preprints"
    assert row["metadata_status"] == "preprints_search"
    assert row["article_type"] == "preprint"
    assert row["is_open_access"] == "true"
    assert row["doi"] == "10.1101/2023.01.01.23000001"
    assert row["title"] == "A preprint on dietary patterns and metabolic health"
    assert row["year"] == "2023"
    assert row["publication_date"] == "2023-01-15"
    assert row["journal"] == "medRxiv"
    assert row["authors"] == "Smith J, Doe A."
    assert row["abstract"] == "We investigated dietary patterns."
    assert row["snippet"] == "We investigated dietary patterns."
    assert row["url"] == "https://doi.org/10.1101/2023.01.01.23000001"
    assert row["query"] == "dietary patterns"
    assert row["provider_query"] == "dietary patterns"
    assert row["oa_pdf_url"] == ""


def test_normalize_preprint_has_all_keys():
    row = _normalize_preprint(_sample_item(), "q")
    assert set(row.keys()) == EXPECTED_KEYS


def test_normalize_preprint_missing_fields_use_empty_strings():
    row = _normalize_preprint({}, "q")
    assert set(row.keys()) == EXPECTED_KEYS
    assert row["doi"] == ""
    assert row["url"] == ""
    assert row["title"] == ""
    assert row["year"] == ""
    # Constants remain populated even on an empty item.
    assert row["article_type"] == "preprint"
    assert row["is_open_access"] == "true"


def test_normalize_preprint_journal_falls_back_to_book_details():
    item = _sample_item()
    del item["journalTitle"]
    item["bookOrReportDetails"] = "Report Series 2023"
    row = _normalize_preprint(item, "q")
    assert row["journal"] == "Report Series 2023"


def test_search_preprints_disabled_network(monkeypatch):
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")
    assert search_preprints("nutrition", limit=5) == []
