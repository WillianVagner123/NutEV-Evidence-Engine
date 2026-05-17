import csv

from nutev.export.curation import _compute_document_key, _curate_row, curate_outputs


def test_compute_document_key_prefixes_pubmed_identifiers():
    pmid_key, pmid_kind = _compute_document_key({"pmid": "12345"})
    pmcid_key, pmcid_kind = _compute_document_key({"pmcid": "PMC12345"})

    assert (pmid_key, pmid_kind) == ("pmid:12345", "pmid")
    assert (pmcid_key, pmcid_kind) == ("pmcid:pmc12345", "pmcid")


def test_curate_row_prioritizes_portuguese_scope_terms():
    curated = _curate_row(
        {
            "document_id": "doc-1",
            "title": "Diretriz de obesidade e risco cardiometabólico",
            "workstream": "busca2a",
            "evidence_type": "guideline",
            "relevance_score": 9,
            "url": "https://example.org/guideline",
        }
    )

    assert curated["is_prioritized"] is True


def test_curate_outputs_writes_empty_contract_files(tmp_path):
    summary = curate_outputs([], tmp_path)

    assert summary == {
        "raw_records": 0,
        "unique_documents": 0,
        "document_workstream_pairs": 0,
    }
    assert (tmp_path / "NUTEV_METADATA_CURATED.csv").exists()
    assert (tmp_path / "NUTEV_DOCUMENTS_UNIQUE.csv").exists()
    assert (tmp_path / "NUTEV_DOCUMENT_WORKSTREAM_MAP.csv").exists()

    with (tmp_path / "NUTEV_DOCUMENTS_UNIQUE.csv").open(encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        header = next(reader)

    assert "document_key" in header
    assert "is_prioritized" in header
