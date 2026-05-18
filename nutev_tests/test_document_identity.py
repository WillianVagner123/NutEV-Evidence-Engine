from nutev.engine.identity import (
    compute_document_key,
    deduplicate_document_rows,
    merge_article_rows,
    normalize_doi,
)


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


def test_deduplicate_document_rows_returns_row_level_audit_manifest():
    deduped_rows, manifest = deduplicate_document_rows(
        [
            {
                "workstream": "busca1",
                "doi": "10.1000/abc",
                "url": "https://example.org/landing",
                "title": "Document A",
                "source": "pubmed",
                "source_provider": "pubmed",
                "year": 2024,
            },
            {
                "workstream": "busca1",
                "doi": "https://doi.org/10.1000/abc",
                "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC1234567/pdf",
                "title": "Document A",
                "source": "europepmc",
                "source_provider": "europepmc",
                "year": 2024,
            },
        ]
    )

    assert len(deduped_rows) == 1
    assert deduped_rows[0]["url"] == "https://pmc.ncbi.nlm.nih.gov/articles/PMC1234567/pdf"

    assert len(manifest) == 2
    winner_row, absorbed_row = manifest

    assert winner_row["document_key"] == "10.1000/abc"
    assert winner_row["document_key_type"] == "doi"
    assert winner_row["occurrence_role"] == "winner"
    assert winner_row["winner_input_index"] == 0
    assert winner_row["absorbed_count"] == 1
    assert winner_row["merge_reason"] == "first_occurrence"
    assert (
        winner_row["winner_url_after_merge"]
        == "https://pmc.ncbi.nlm.nih.gov/articles/PMC1234567/pdf"
    )

    assert absorbed_row["occurrence_role"] == "absorbed"
    assert absorbed_row["winner_input_index"] == 0
    assert absorbed_row["merge_reason"] == "absorbed_by_same_doi"
    assert absorbed_row["dedup_rule"] == "same_doi"
