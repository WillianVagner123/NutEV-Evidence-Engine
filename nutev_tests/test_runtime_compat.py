"""Regression tests for behaviour formerly injected by the runtime_compat shim.

The shim was fully dissolved into first-class code
(docs/REFACTOR_RUNTIME_COMPAT_MIGRATION.md); these tests pin the behaviour that
mattered: ``global_watch`` is a valid workstream (was
``_patch_workstream_validation``), and the audit artifacts count
``evidence_claims_inference_only`` — claims that are NOT quote-backed must be
counted, not silently dropped from the summary.
"""
from __future__ import annotations

from pathlib import Path


def test_runtime_compat_module_is_gone():
    # The shim and its auto-load sitecustomize were retired; nothing imports them.
    import importlib.util

    assert importlib.util.find_spec("nutev.runtime_compat") is None


def test_global_watch_is_a_valid_workstream_natively():
    from nutev.engine.validators import validate_workstream

    # Was _patch_workstream_validation; now native in engine.validators.
    assert validate_workstream("global_watch") == "global_watch"


def test_audit_artifacts_report_inference_only(tmp_path: Path):
    from nutev.export.audit_artifacts import write_audit_artifacts

    quote = (
        "Clinicians should recommend a mediterranean dietary pattern to reduce "
        "cardiometabolic risk in adults."
    )
    rows = [
        # Quote-backed: sentence present verbatim in extracted_text -> supported.
        {"document_id": "d1", "title": "Title ends here.", "abstract": "", "extracted_text": quote},
        # Metadata-only (no extracted text) -> inference_only, needs review.
        {
            "document_id": "d2",
            "title": "A guideline should advise adults to reduce sodium intake overall.",
            "abstract": "",
            "extracted_text": "",
        },
    ]
    summary = write_audit_artifacts(rows, tmp_path)
    assert summary["evidence_claims_supported"] >= 1
    assert summary["evidence_claims_inference_only"] >= 1
    # Total must equal supported + inference_only (no claim is uncounted).
    assert (
        summary["evidence_claims_total"]
        == summary["evidence_claims_supported"] + summary["evidence_claims_inference_only"]
    )


def test_missing_ocr_dependencies_reports_actionable_items(monkeypatch):
    """When OCR prerequisites are absent, the pipeline names what to install."""
    from nutev.extract import pdf_text

    # Simulate a machine with no PyMuPDF, no poppler, and no tesseract on PATH.
    monkeypatch.setattr(pdf_text, "_has_pymupdf", lambda: False)
    monkeypatch.setattr(pdf_text.shutil, "which", lambda _name: None)
    missing = pdf_text.missing_ocr_dependencies()
    joined = " ".join(missing)
    # Rendering guidance offers the pip-only path first (pymupdf).
    assert "pymupdf" in joined
    assert "tesseract" in joined
    # Every item must tell the user how to obtain it.
    assert all(("install" in m or "documents" in m or "pymupdf" in m) for m in missing)


def test_ocr_rendering_satisfied_by_pymupdf_without_poppler(monkeypatch):
    """With PyMuPDF present, poppler is NOT required for PDF rendering."""
    from nutev.extract import pdf_text

    monkeypatch.setattr(pdf_text, "_has_pymupdf", lambda: True)
    # No poppler on PATH, but tesseract present (as on the user's machine).
    monkeypatch.setattr(pdf_text.shutil, "which", lambda name: "/usr/bin/tesseract" if name == "tesseract" else None)
    missing = pdf_text.missing_ocr_dependencies()
    joined = " ".join(missing)
    assert "PDF rendering" not in joined  # PyMuPDF covers it, no poppler needed
