"""Regression tests for the deterministic runtime-compat bootstrap.

Two things must hold for reproducible local runs:

1. ``nutev.runtime_compat.apply()`` applies the remaining pipeline hooks
   (synthesis defaults, workstream validation) explicitly and idempotently, so
   behaviour does not depend on ``sitecustomize.py`` being auto-imported. The
   query-generation (Phase 1) and curation/run-summary (Phase 2) patches were
   dissolved into first-class code — see docs/REFACTOR_RUNTIME_COMPAT_MIGRATION.md.
2. The audit artifacts report ``evidence_claims_inference_only`` — claims that
   are NOT quote-backed must be counted, not silently dropped from the summary.
"""
from __future__ import annotations

from pathlib import Path


def test_apply_is_idempotent_and_no_longer_patches_curation():
    from nutev.engine.validators import validate_workstream
    from nutev.export import curation
    from nutev.runtime_compat import apply

    apply()
    apply()  # second call must be a no-op, not double-wrap
    # Curation is no longer monkey-patched (Phase 2 moved it to curation_finalize).
    assert not hasattr(curation.curate_outputs, "_nutev_audit_patched")
    # A still-active hook proves apply() ran: global_watch is accepted as a workstream.
    assert validate_workstream("global_watch") == "global_watch"


def test_sitecustomize_delegates_to_runtime_compat():
    text = Path("src/sitecustomize.py").read_text(encoding="utf-8")
    # The real logic must live in the importable module, not be duplicated here.
    assert "nutev.runtime_compat" in text
    assert "_patch_curation" not in text


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
