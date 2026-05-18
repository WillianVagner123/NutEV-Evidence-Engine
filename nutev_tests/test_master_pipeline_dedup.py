from nutev.pipelines.master_pipeline import _dedup_rows, _dedup_rows_with_manifest


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


def test_dedup_rows_with_manifest_explains_winner_and_absorbed_rows():
    rows = [
        {
            "workstream": "busca1",
            "title": "Lifestyle medicine obesity guideline",
            "doi": "10.1000/abc",
            "url": "https://doi.org/10.1000/abc",
            "source": "pubmed",
            "year": 2024,
        },
        {
            "workstream": "busca1",
            "title": "Lifestyle medicine obesity guideline",
            "doi": "https://doi.org/10.1000/abc",
            "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC1234567/pdf",
            "source": "europepmc",
            "year": "2024",
        },
    ]

    deduped, manifest = _dedup_rows_with_manifest(rows)

    assert len(deduped) == 1
    assert len(manifest) == 2
    assert manifest[0]["occurrence_role"] == "winner"
    assert manifest[0]["dedup_rule"] == "same_doi"
    assert manifest[0]["absorbed_count"] == 1
    assert manifest[1]["occurrence_role"] == "absorbed"
    assert manifest[1]["merge_reason"] == "absorbed_by_same_doi"
    assert manifest[1]["winner_input_index"] == 0
    assert (
        manifest[1]["winner_url_after_merge"]
        == "https://pmc.ncbi.nlm.nih.gov/articles/PMC1234567/pdf"
    )
