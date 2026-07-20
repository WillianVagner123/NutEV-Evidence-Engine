import csv
import importlib.util

import pandas as pd

from nutev.export.curation import curate_outputs
from nutev.export.curation_finalize import finalize_curated_layer


def test_curated_outputs_deduplicate_and_map_workstreams(tmp_path):
    rows = [
        {
            "document_id": "doc_1",
            "title": "Obesity guideline",
            "doi": "10.1000/ABC",
            "original_url": "https://example.org/a",
            "final_url": "https://example.org/a",
            "workstream": "busca1",
            "year": 2024,
            "evidence_type": "guideline",
            "download_status": "pdf",
            "capture_status": "pdf",
            "extraction_status": "ok",
            "relevance_score": 10,
        },
        {
            "document_id": "doc_2",
            "title": "Obesity guideline update",
            "doi": "https://doi.org/10.1000/abc",
            "original_url": "https://example.org/b",
            "final_url": "https://example.org/b",
            "workstream": "busca2a",
            "year": 2024,
            "evidence_type": "guideline",
            "download_status": "metadata_only",
            "capture_status": "metadata_only",
            "extraction_status": "missing",
            "relevance_score": 9,
        },
        {
            "document_id": "doc_3",
            "title": "Food literacy framework",
            "original_url": "https://example.org/c",
            "final_url": "https://example.org/c",
            "workstream": "a3",
            "year": 2025,
            "evidence_type": "framework",
            "download_status": "html_snapshot",
            "capture_status": "html_snapshot",
            "extraction_status": "ok",
            "relevance_score": 9,
        },
        {
            "document_id": "doc_4",
            "title": "",
            "original_url": "",
            "final_url": "",
            "workstream": "busca2b",
            "year": "",
            "evidence_type": "",
            "download_status": "metadata_only",
            "capture_status": "metadata_only",
            "extraction_status": "missing",
            "relevance_score": 1,
        },
    ]

    summary = curate_outputs(rows, tmp_path)
    finalize_curated_layer(rows, tmp_path, summary)

    assert summary["raw_records"] == 4
    assert summary["unique_documents"] == 3
    assert (tmp_path / "NUTEV_METADATA_CURATED.csv").exists()
    assert (tmp_path / "NUTEV_DOCUMENTS_UNIQUE.csv").exists()
    assert (tmp_path / "NUTEV_DOCUMENT_WORKSTREAM_MAP.csv").exists()
    assert (tmp_path / "NUTEV_QA_REPORT.xlsx").exists()
    assert (tmp_path / "NUTEV_PRISMA_FLOW_CORRIGIDO.xlsx").exists()

    with (tmp_path / "NUTEV_DOCUMENTS_UNIQUE.csv").open(encoding="utf-8-sig") as handle:
        unique_rows = list(csv.DictReader(handle))
    assert len(unique_rows) == 3
    assert any(row["document_key"] == "10.1000/abc" for row in unique_rows)

    with (tmp_path / "NUTEV_DOCUMENT_WORKSTREAM_MAP.csv").open(encoding="utf-8-sig") as handle:
        map_rows = list(csv.DictReader(handle))
    doi_rows = [row for row in map_rows if row["document_key"] == "10.1000/abc"]
    assert sorted(row["workstream"] for row in doi_rows) == ["busca1", "busca2a"]

    if importlib.util.find_spec("openpyxl") is not None:
        prisma = pd.read_excel(tmp_path / "NUTEV_PRISMA_FLOW_CORRIGIDO.xlsx", sheet_name="flow")
        assert int(prisma.loc[0, "registros_identificados"]) == 4
        assert int(prisma.loc[0, "registros_triados"]) == 3

        duplicate_summary = pd.read_excel(tmp_path / "NUTEV_QA_REPORT.xlsx", sheet_name="duplicate_summary")
        assert "document_key_type" in duplicate_summary.columns
        assert int(duplicate_summary.loc[0, "duplicate_documents"]) == 1

        missing_by_workstream = pd.read_excel(tmp_path / "NUTEV_QA_REPORT.xlsx", sheet_name="missing_by_workstream")
        busca2b = missing_by_workstream[missing_by_workstream["workstream"] == "busca2b"].iloc[0]
        assert int(busca2b["missing_title"]) == 1
        assert int(busca2b["missing_url"]) == 1


def test_curated_outputs_write_headers_when_empty(tmp_path):
    summary = curate_outputs([], tmp_path)
    finalize_curated_layer([], tmp_path, summary)
    assert summary["raw_records"] == 0
    with (tmp_path / "NUTEV_METADATA_CURATED.csv").open(encoding="utf-8-sig") as handle:
        header = next(handle).strip()
    assert "document_key" in header
    with (tmp_path / "NUTEV_DOCUMENTS_UNIQUE.csv").open(encoding="utf-8-sig") as handle:
        header = next(handle).strip()
    assert "document_key" in header
