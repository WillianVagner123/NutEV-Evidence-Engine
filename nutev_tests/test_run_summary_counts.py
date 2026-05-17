from nutev.pipelines.master_pipeline import _build_operational_counts


def test_build_operational_counts_tracks_raw_unique_and_pairs():
    rows = [
        {
            "doi": "10.1000/abc",
            "workstream": "busca1",
            "title": "Obesity guideline",
        },
        {
            "doi": "https://doi.org/10.1000/abc",
            "workstream": "busca2a",
            "title": "Obesity guideline duplicate",
        },
        {
            "url": "https://example.org/c",
            "workstream": "busca2a",
            "title": "Diet adherence study",
            "year": 2024,
        },
    ]

    counts = _build_operational_counts(rows)

    assert counts["raw_records"] == 3
    assert counts["unique_documents"] == 2
    assert counts["document_workstream_pairs"] == 3
    assert counts["workstream_summary"]["busca1"] == {
        "raw_records": 1,
        "unique_documents": 1,
        "document_workstream_pairs": 1,
    }
    assert counts["workstream_summary"]["busca2a"] == {
        "raw_records": 2,
        "unique_documents": 2,
        "document_workstream_pairs": 2,
    }
