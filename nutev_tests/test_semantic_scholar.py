from __future__ import annotations

from nutev.search.semantic_scholar import (
    _normalize_semantic_scholar,
    search_semantic_scholar,
)

SAMPLE_ITEM = {
    "title": "Plant-Based Diets and Cardiometabolic Health",
    "abstract": "A" * 450,
    "year": 2021,
    "venue": "Journal of Nutrition",
    "externalIds": {
        "DOI": "https://doi.org/10.1234/ABC.2021.0001",
        "PubMed": "34567890",
        "PubMedCentral": "PMC8123456",
    },
    "openAccessPdf": {"url": "https://example.org/paper.pdf"},
    "authors": [
        {"name": "Jane Doe"},
        {"name": "John Smith"},
    ]
    + [{"name": f"Author {i}"} for i in range(20)],
    "publicationTypes": ["JournalArticle", "Review"],
    "url": "https://www.semanticscholar.org/paper/abc123",
}


def test_normalize_schema_and_values():
    row = _normalize_semantic_scholar(SAMPLE_ITEM, "plant based diet")

    expected_keys = {
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
    assert set(row.keys()) == expected_keys

    assert row["source"] == "semantic_scholar"
    assert row["source_provider"] == "semantic_scholar"
    assert row["metadata_status"] == "semantic_scholar_search"
    assert row["query"] == "plant based diet"
    assert row["provider_query"] == "plant based diet"

    # DOI stripped of https://doi.org/ prefix and lowercased.
    assert row["doi"] == "10.1234/abc.2021.0001"

    assert row["pmid"] == "34567890"
    assert row["pmcid"] == "PMC8123456"

    # openAccessPdf -> oa_pdf_url set, is_open_access true.
    assert row["oa_pdf_url"] == "https://example.org/paper.pdf"
    assert row["is_open_access"] == "true"

    # url prefers the landing url.
    assert row["url"] == "https://www.semanticscholar.org/paper/abc123"

    assert row["journal"] == "Journal of Nutrition"
    assert row["year"] == "2021"
    assert row["publication_date"] == "2021"
    assert row["article_type"] == "JournalArticle; Review"

    # Authors joined with "; " and capped at 12.
    assert row["authors"].startswith("Jane Doe; John Smith; ")
    assert len(row["authors"].split("; ")) == 12

    # snippet truncated to ~300 chars.
    assert len(row["snippet"]) == 300


def test_normalize_missing_fields_use_empty_strings():
    row = _normalize_semantic_scholar({}, "q")
    for key in (
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
        "oa_pdf_url",
    ):
        assert row[key] == ""
    assert row["is_open_access"] == "false"


def test_search_disabled_network_returns_empty(monkeypatch):
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")
    assert search_semantic_scholar("anything") == []
