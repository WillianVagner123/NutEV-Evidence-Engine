"""Phase 1 perf: render-on-demand generator + content-addressed OCR cache."""
from __future__ import annotations

import logging
import types

import pytest

import nutev.extract.smart_extract as se

_LOG = logging.getLogger("test")


def _make_image_pdf(path, pages: int = 2):
    fitz = pytest.importorskip("fitz")
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (300, 120), "white")
    ImageDraw.Draw(img).text((10, 50), "guia", fill="black")
    imgp = path.parent / "_p.png"
    img.save(imgp)
    doc = fitz.open()
    for _ in range(pages):
        pg = doc.new_page(width=300, height=120)
        pg.insert_image(fitz.Rect(0, 0, 300, 120), filename=str(imgp))
    doc.save(str(path))
    doc.close()


def test_render_pdf_pages_is_lazy_generator(tmp_path):
    from nutev.extract.pdf_text import _render_pdf_pages

    pdf = tmp_path / "scan.pdf"
    _make_image_pdf(pdf, pages=2)
    gen = _render_pdf_pages(pdf, dpi=120)
    # It's a generator (renders on demand), not a pre-built list.
    assert isinstance(gen, types.GeneratorType)
    imgs = list(gen)
    assert len(imgs) == 2
    assert imgs[0].size[0] > 0


def test_ocr_cache_avoids_second_ocr(tmp_path, monkeypatch):
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake body")
    ocr_dir = tmp_path / "04_ocr"
    out_dir = tmp_path / "05_extract"

    monkeypatch.setattr(se, "is_probably_pdf_file", lambda _p: True)
    monkeypatch.setattr(se, "extract_pdf_text_pages", lambda _p: [])  # force OCR path

    calls = {"n": 0}

    def fake_ocr(path, logger):
        calls["n"] += 1
        return ["National dietary guideline about diet quality and adherence, OCR page one."], []

    monkeypatch.setattr(se, "ocr_scanned_pdf_pages", fake_ocr)

    first = se.extract_document(pdf, ocr_dir, out_dir, _LOG, capture_pages=True)
    second = se.extract_document(pdf, ocr_dir, out_dir, _LOG, capture_pages=True)

    assert calls["n"] == 1  # the second run reused the cache (no re-OCR)
    assert first["extraction_status"] == second["extraction_status"] == "ok_ocr"
    assert first["pages"] == second["pages"]  # identical output from the cache


def test_ocr_cache_invalidated_by_settings_signature(tmp_path, monkeypatch):
    # A different OCR settings signature must not reuse an old cache entry.
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake body")
    ocr_dir = tmp_path / "04_ocr"
    out_dir = tmp_path / "05_extract"
    monkeypatch.setattr(se, "is_probably_pdf_file", lambda _p: True)
    monkeypatch.setattr(se, "extract_pdf_text_pages", lambda _p: [])

    calls = {"n": 0}

    def fake_ocr(path, logger):
        calls["n"] += 1
        return ["National dietary guideline about diet quality and adherence, OCR page one."], []

    monkeypatch.setattr(se, "ocr_scanned_pdf_pages", fake_ocr)

    monkeypatch.setattr(se, "ocr_cache_signature", lambda: "sigAAAAAA")
    se.extract_document(pdf, ocr_dir, out_dir, _LOG, capture_pages=True)
    monkeypatch.setattr(se, "ocr_cache_signature", lambda: "sigBBBBBB")
    se.extract_document(pdf, ocr_dir, out_dir, _LOG, capture_pages=True)

    assert calls["n"] == 2  # settings changed -> cache not reused
