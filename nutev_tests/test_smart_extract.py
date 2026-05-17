import logging

from nutev.extract.smart_extract import extract_document


def test_pdf_uses_ocr_when_native_text_is_too_short(tmp_path, monkeypatch):
    pdf_path = tmp_path / "scan.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n")

    monkeypatch.setattr("nutev.extract.smart_extract.is_probably_pdf_file", lambda _: True)
    monkeypatch.setattr("nutev.extract.smart_extract.extract_pdf_text", lambda _: ("short text", True))
    monkeypatch.setattr(
        "nutev.extract.smart_extract.ocr_scanned_pdf",
        lambda _path, _logger: ("ocr body text " * 20, [], None),
    )

    result = extract_document(
        pdf_path,
        tmp_path / "04_ocr_text",
        tmp_path / "05_extraction",
        logging.getLogger("test"),
    )

    assert result["used_ocr"] is True
    assert result["ocr_attempted"] is True
    assert result["extraction_status"] == "ok_ocr"
    assert result["chars"] > 120


def test_pdf_marks_ocr_unavailable_when_tesseract_is_missing(tmp_path, monkeypatch):
    pdf_path = tmp_path / "scan.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n")

    monkeypatch.setattr("nutev.extract.smart_extract.is_probably_pdf_file", lambda _: True)
    monkeypatch.setattr("nutev.extract.smart_extract.extract_pdf_text", lambda _: ("", False))
    monkeypatch.setattr(
        "nutev.extract.smart_extract.ocr_scanned_pdf",
        lambda _path, _logger: ("", [], "tesseract_missing"),
    )

    result = extract_document(
        pdf_path,
        tmp_path / "04_ocr_text",
        tmp_path / "05_extraction",
        logging.getLogger("test"),
    )

    assert result["used_ocr"] is False
    assert result["ocr_attempted"] is True
    assert result["extraction_status"] == "ocr_unavailable"
    assert result["failure_reason"] == "tesseract_missing"


def test_pdf_keeps_native_text_when_it_is_already_usable(tmp_path, monkeypatch):
    pdf_path = tmp_path / "native.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n")
    native_text = "Lifestyle medicine dietary pattern adherence " * 10

    monkeypatch.setattr("nutev.extract.smart_extract.is_probably_pdf_file", lambda _: True)
    monkeypatch.setattr("nutev.extract.smart_extract.extract_pdf_text", lambda _: (native_text, True))

    def _unexpected_ocr(*_args, **_kwargs):
        raise AssertionError("OCR should not run when native text is usable")

    monkeypatch.setattr("nutev.extract.smart_extract.ocr_scanned_pdf", _unexpected_ocr)

    result = extract_document(
        pdf_path,
        tmp_path / "04_ocr_text",
        tmp_path / "05_extraction",
        logging.getLogger("test"),
    )

    assert result["used_ocr"] is False
    assert result["ocr_attempted"] is False
    assert result["extraction_status"] == "ok"
    assert result["chars"] == len(native_text)
