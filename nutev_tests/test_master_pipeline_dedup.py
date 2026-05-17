from nutev.pipelines.master_pipeline import _dedup_rows


def test_dedup_rows_collapses_same_doi_and_keeps_better_capture_url():
    rows = [
        {
            "title": "Lifestyle medicine obesity guideline",
            "doi": "10.1000/abc",
            "url": "https://doi.org/10.1000/abc",
            "source": "pubmed",
        },
        {
            "title": "Lifestyle medicine obesity guideline",
            "doi": "https://doi.org/10.1000/abc",
            "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC1234567/pdf",
            "source": "europepmc",
            "abstract": "Longer abstract with more detail.",
        },
    ]

    deduped = _dedup_rows(rows)

    assert len(deduped) == 1
    assert deduped[0]["url"] == "https://pmc.ncbi.nlm.nih.gov/articles/PMC1234567/pdf"
    assert deduped[0]["abstract"] == "Longer abstract with more detail."


def test_dedup_rows_uses_title_year_when_identifiers_are_missing():
    rows = [
        {
            "title": "Diet adherence implementation study",
            "year": 2024,
            "url": "https://example.org/a",
        },
        {
            "title": "Diet adherence implementation study",
            "year": "2024",
            "url": "https://example.org/b",
        },
    ]

    deduped = _dedup_rows(rows)

    assert len(deduped) == 1
