"""P3+ — OCR failure detector and retry-at-higher-DPI."""
from __future__ import annotations

import logging

import nutev.extract.pdf_text as pdf_text
from nutev.extract.pdf_text import ocr_output_looks_failed

_LOG = logging.getLogger("test")


def test_failure_detector():
    assert ocr_output_looks_failed("") is True
    assert ocr_output_looks_failed("   ") is True
    assert ocr_output_looks_failed("@#$%^&*()_+{}|:<>?~`") is True   # symbol soup
    assert ocr_output_looks_failed("short") is True                  # too short
    good = "This national dietary guideline recommends increasing vegetable intake."
    assert ocr_output_looks_failed(good) is False


def test_retry_at_higher_dpi_recovers(monkeypatch, tmp_path):
    # A "scanned" PDF: 200 DPI yields garbage, 400 DPI yields good text.
    p = tmp_path / "scan.pdf"
    p.write_bytes(b"%PDF-1.4 fake")
    monkeypatch.setattr(pdf_text, "is_probably_pdf_file", lambda _p: True)

    calls = {"dpi": []}

    def fake_ocr_at_dpi(path, dpi, logger):
        calls["dpi"].append(dpi)
        if dpi == 200:
            return "@#$%^&*()", []       # garbage -> looks failed
        return "Proper readable guideline text about diet quality and adherence.", []

    monkeypatch.setattr(pdf_text, "_ocr_at_dpi", fake_ocr_at_dpi)
    text, failed = pdf_text.ocr_scanned_pdf(p, _LOG)
    assert "readable guideline" in text
    assert calls["dpi"] == [200, 400]   # retried at higher DPI


def test_no_retry_when_first_pass_is_good(monkeypatch, tmp_path):
    p = tmp_path / "scan.pdf"
    p.write_bytes(b"%PDF-1.4 fake")
    monkeypatch.setattr(pdf_text, "is_probably_pdf_file", lambda _p: True)

    calls = {"dpi": []}

    def fake_ocr_at_dpi(path, dpi, logger):
        calls["dpi"].append(dpi)
        return "Good dietary guideline text recommending more fruit and vegetables.", []

    monkeypatch.setattr(pdf_text, "_ocr_at_dpi", fake_ocr_at_dpi)
    text, _ = pdf_text.ocr_scanned_pdf(p, _LOG)
    assert "Good dietary guideline" in text
    assert calls["dpi"] == [200]        # first pass sufficient, no retry
