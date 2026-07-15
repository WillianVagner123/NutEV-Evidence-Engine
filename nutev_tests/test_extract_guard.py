"""P4 — the extraction guard: no silent empty text files."""
from __future__ import annotations

import logging
from pathlib import Path

from nutev.extract.smart_extract import extract_document

_LOG = logging.getLogger("test")


def test_no_txt_written_when_no_usable_text(tmp_path: Path):
    # An empty input yields no usable text -> status must not be a success and
    # NO .txt file may be written (the 11-33 byte silent-file bug).
    src = tmp_path / "empty.txt"
    src.write_text("", encoding="utf-8")
    out_dir = tmp_path / "05"
    ocr_dir = tmp_path / "04"
    result = extract_document(src, ocr_dir, out_dir, _LOG)

    assert result["extraction_status"] not in {"ok", "ok_ocr", "fake_pdf_html", "fake_pdf_text"}
    assert result["text_path"] == ""
    # No stray .txt artifact was created.
    assert list(out_dir.glob("*.txt")) == []


def test_txt_written_only_when_text_is_usable(tmp_path: Path):
    src = tmp_path / "good.txt"
    body = "This guideline recommends increasing vegetable intake for adults. " * 10
    src.write_text(body, encoding="utf-8")
    out_dir = tmp_path / "05"
    ocr_dir = tmp_path / "04"
    result = extract_document(src, ocr_dir, out_dir, _LOG)

    assert result["extraction_status"] == "ok"
    assert result["text_path"] and Path(result["text_path"]).exists()
    assert Path(result["text_path"]).read_text(encoding="utf-8").strip()
    assert result["chars"] > 0
