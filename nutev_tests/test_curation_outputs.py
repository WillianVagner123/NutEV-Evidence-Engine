import importlib.util

from nutev.analysis.prisma import build_prisma_flow
from nutev.export.curation import write_curated_outputs


def test_build_prisma_flow_counts_unique_documents():
    rows = [
        {
            "doi": "10.1000/test",
            "title": "Doc A",
            "workstream": "busca1",
            "file_path": "/tmp/a.pdf",
            "extraction_status": "ok_ocr",
            "domains": "obesidade",
            "relevance_score": 9,
        },
        {
            "doi": "10.1000/test",
            "title": "Doc A duplicate",
            "workstream": "busca2a",
            "file_path": "",
            "extraction_status": "missing",
            "domains": "",
            "relevance_score": 4,
        },
        {
            "url": "https://example.org/b",
            "title": "Doc B",
            "workstream": "a3",
            "file_path": "",
            "extraction_status": "missing",
            "domains": "",
            "relevance_score": 3,
        },
    ]

    flow = build_prisma_flow(rows, [{"path": "/tmp/a.pdf"}], [{"file": "/tmp/a.pdf", "extraction_status": "ok_ocr"}])

    assert flow["registros_identificados"] == 3
    assert flow["duplicados_removidos"] == 1
    assert flow["registros_triados"] == 2
    assert flow["documentos_com_pdf_ou_html"] == 1
    assert flow["documentos_metadata_only"] == 1
    assert flow["documentos_priorizados"] == 1


def test_write_curated_outputs_generates_expected_files(tmp_path):
    if importlib.util.find_spec("openpyxl") is None:
        return

    all_rows = [
        {
            "document_id": "doc_a",
            "doi": "10.1000/test",
            "title": "Doc A",
            "workstream": "busca1",
            "source": "pubmed",
            "source_provider": "pubmed",
            "url": "https://example.org/a",
            "file_path": str(tmp_path / "a.pdf"),
            "relevance_score": 9,
            "domains": "obesidade",
            "nutev_objects": "evidence_table",
            "ocr_attempted": True,
            "used_ocr": True,
            "ocr_failed_pages": "",
            "extraction_status": "ok_ocr",
            "extraction_failure_reason": "",
            "year": 2024,
        },
        {
            "document_id": "doc_a_dup",
            "doi": "10.1000/test",
            "title": "Doc A Duplicate",
            "workstream": "busca2a",
            "source": "crossref",
            "source_provider": "crossref",
            "url": "https://doi.org/10.1000/test",
            "file_path": "",
            "relevance_score": 7,
            "domains": "obesidade",
            "nutev_objects": "evidence_table",
            "ocr_attempted": False,
            "used_ocr": False,
            "ocr_failed_pages": "",
            "extraction_status": "missing",
            "extraction_failure_reason": "",
            "year": 2024,
        },
        {
            "document_id": "doc_b",
            "title": "Doc B",
            "workstream": "a3",
            "source": "official_web",
            "source_provider": "official_web",
            "url": "https://example.org/b",
            "file_path": "",
            "relevance_score": 4,
            "domains": "",
            "nutev_objects": "",
            "ocr_attempted": True,
            "used_ocr": False,
            "ocr_failed_pages": "1;2",
            "extraction_status": "ocr_unavailable",
            "extraction_failure_reason": "tesseract_missing",
            "year": 2023,
        },
    ]
    extraction_manifest = [
        {
            "file": str(tmp_path / "a.pdf"),
            "used_ocr": True,
            "ocr_attempted": True,
            "ocr_failed_pages": "",
            "extraction_status": "ok_ocr",
            "failure_reason": "",
        }
    ]

    outputs = write_curated_outputs(all_rows, [{"path": str(tmp_path / "a.pdf")}], extraction_manifest, tmp_path / "10_curated")

    assert (tmp_path / "10_curated" / "NUTEV_METADATA_CURATED.csv").exists()
    assert (tmp_path / "10_curated" / "NUTEV_METADATA_CURATED.xlsx").exists()
    assert (tmp_path / "10_curated" / "NUTEV_DOCUMENTS_UNIQUE.csv").exists()
    assert (tmp_path / "10_curated" / "NUTEV_DOCUMENTS_UNIQUE.xlsx").exists()
    assert (tmp_path / "10_curated" / "NUTEV_DOCUMENT_WORKSTREAM_MAP.csv").exists()
    assert (tmp_path / "10_curated" / "NUTEV_QA_REPORT.xlsx").exists()
    assert (tmp_path / "10_curated" / "NUTEV_PRISMA_FLOW_CORRIGIDO.xlsx").exists()

    assert len(outputs["unique_documents"]) == 2
    assert len(outputs["workstream_map"]) == 3
    assert outputs["prisma_flow"]["registros_triados"] == 2
    assert outputs["prisma_flow"]["documentos_com_pdf_ou_html"] == 1
    assert outputs["prisma_flow"]["documentos_metadata_only"] == 1

    qa_summary = outputs["qa_sheets"]["summary"]
    metrics = dict(zip(qa_summary["metric"], qa_summary["value"]))
    assert metrics["ocr_docs"] == 1
    assert metrics["ocr_unavailable"] == 1
    assert metrics["duplicates_removed"] == 1
