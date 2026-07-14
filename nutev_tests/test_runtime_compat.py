"""Regression tests for the deterministic runtime-compat bootstrap.

Two things must hold for reproducible local runs:

1. ``nutev.runtime_compat.apply()`` applies the pipeline hooks (curation,
   run-summary, synthesis, query generation, workstream validation) explicitly,
   so behaviour does not depend on ``sitecustomize.py`` being auto-imported.
2. The audit artifacts report ``evidence_claims_inference_only`` — claims that
   are NOT quote-backed must be counted, not silently dropped from the summary.
"""
from __future__ import annotations

from pathlib import Path


def test_apply_is_idempotent_and_patches_curation():
    from nutev.export import curation
    from nutev.runtime_compat import apply

    apply()
    apply()  # second call must be a no-op, not double-wrap
    assert getattr(curation.curate_outputs, "_nutev_audit_patched", False) is True


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
    import shutil as _shutil

    from nutev.extract import pdf_text

    # Simulate a machine with neither poppler nor tesseract on PATH.
    monkeypatch.setattr(pdf_text.shutil, "which", lambda _name: None)
    missing = pdf_text.missing_ocr_dependencies()
    joined = " ".join(missing)
    assert "poppler" in joined
    assert "tesseract" in joined
    # Every item must tell the user how to obtain it.
    assert all(("install" in m or "documents" in m) for m in missing)
