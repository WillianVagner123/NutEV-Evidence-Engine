from __future__ import annotations

from pathlib import Path

from nutev.export.curation import curate_outputs


def test_curate_outputs_writes_canonical_and_legacy_files(tmp_path: Path) -> None:
    rows = [
        {
            "document_id": "doc-1",
            "title": "Clinical practice guideline for obesity and cardiometabolic risk",
            "year": "2024",
            "workstream": "busca2a",
            "evidence_type": "guideline",
            "source": "pubmed",
            "url": "https://example.org/guideline.pdf",
            "download_status": "pdf",
            "capture_status": "ok",
            "extraction_status": "ok",
            "relevance_score": 14,
            "editorial_priority_score": 8,
            "editorial_priority_tier": "a1_proxy_moderate",
        },
        {
            "document_id": "doc-2",
            "title": "Clinical practice guideline for obesity and cardiometabolic risk",
            "year": "2024",
            "workstream": "busca2b",
            "evidence_type": "guideline",
            "source": "europepmc",
            "url": "https://example.org/guideline.pdf",
            "download_status": "metadata_only",
            "capture_status": "missing",
            "extraction_status": "missing",
            "relevance_score": 10,
        },
    ]

    summary = curate_outputs(rows, tmp_path)

    expected_files = [
        "curated_metadata.csv",
        "curated_metadata.xlsx",
        "unique_documents.csv",
        "unique_documents.xlsx",
        "workstream_document_map.csv",
        "top_operational_documents.xlsx",
        "NUTEV_METADATA_CURATED.csv",
        "NUTEV_METADATA_CURATED.xlsx",
        "NUTEV_DOCUMENTS_UNIQUE.csv",
        "NUTEV_DOCUMENTS_UNIQUE.xlsx",
        "NUTEV_DOCUMENT_WORKSTREAM_MAP.csv",
        "NUTEV_DOCUMENT_WORKSTREAM_MAP.xlsx",
        "NUTEV_QA_REPORT.xlsx",
        "NUTEV_PRISMA_FLOW_CORRIGIDO.xlsx",
        "curation_summary.json",
    ]
    for filename in expected_files:
        assert (tmp_path / filename).exists(), filename

    assert summary["curated_rows"] == 2
    assert summary["unique_documents"] == 1
    assert summary["prioritized_documents"] == 1
    assert summary["metadata_only_documents"] == 0


def test_curate_outputs_prioritizes_ultra_processed_nova_records(tmp_path: Path) -> None:
    rows = [
        {
            "document_id": "doc-upf",
            "title": "NOVA classification and ultra-processed foods in cardiometabolic risk",
            "year": "2025",
            "workstream": "busca2b",
            "evidence_type": "systematic review",
            "source": "pubmed",
            "url": "https://example.org/upf-review",
            "download_status": "metadata_only",
            "capture_status": "missing",
            "extraction_status": "missing",
            "relevance_score": 8,
        },
    ]

    summary = curate_outputs(rows, tmp_path)

    assert summary["prioritized_documents"] == 1
