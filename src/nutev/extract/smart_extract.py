from __future__ import annotations

from pathlib import Path

from nutev.extract.docx_text import extract_docx_text
from nutev.extract.html_text import extract_html_text
from nutev.extract.image_ocr import ocr_image
from nutev.extract.pdf_text import (
    extract_pdf_text,
    is_probably_pdf_file,
    ocr_scanned_pdf,
    should_run_ocr_fallback,
)
from nutev.extract.spreadsheet_text import extract_csv_text, extract_sheet_text


def _read_text_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _extract_html_file(path: Path) -> str:
    raw = _read_text_safe(path)
    payload = extract_html_text(raw)
    return "\n".join(
        [
            payload.get("title", ""),
            *payload.get("headings", []),
            payload.get("body", ""),
        ]
    ).strip()


def _looks_like_html_bytes(path: Path) -> bool:
    try:
        head = path.read_bytes()[:4096].lower()
        return b"<html" in head or b"<!doctype html" in head or b"<body" in head
    except Exception:
        return False


def extract_document(path: Path, ocr_dir: Path, out_dir: Path, logger) -> dict:
    ext = path.suffix.lower().lstrip(".")
    text = ""
    used_ocr = False
    ocr_attempted = False
    ocr_failed_pages: list[int] = []
    extraction_status = "empty"
    failure_reason = ""

    if ext == "pdf":
        if is_probably_pdf_file(path):
            text, _ = extract_pdf_text(path)
            if should_run_ocr_fallback(text):
                ocr_attempted = True
                ocr_text, ocr_failed_pages, ocr_failure_reason = ocr_scanned_pdf(path, logger)
                if ocr_text:
                    text = ocr_text
                    used_ocr = True
                    extraction_status = "ok_ocr"
                elif text:
                    extraction_status = "ok_native_low_confidence"
                    failure_reason = ocr_failure_reason or "ocr_not_improved"
                else:
                    extraction_status = "ocr_unavailable" if ocr_failure_reason == "tesseract_missing" else "pdf_no_text"
                    failure_reason = ocr_failure_reason or "pdf_no_text"
            else:
                extraction_status = "ok"
        elif _looks_like_html_bytes(path):
            text = _extract_html_file(path)
            extraction_status = "fake_pdf_html"
        else:
            text = _read_text_safe(path)
            extraction_status = "fake_pdf_text"

    elif ext == "docx":
        text = extract_docx_text(path)
        extraction_status = "ok" if text else "empty"

    elif ext in {"xlsx", "xls"}:
        text, _ = extract_sheet_text(path)
        extraction_status = "ok" if text else "empty"

    elif ext == "csv":
        text, _ = extract_csv_text(path)
        extraction_status = "ok" if text else "empty"

    elif ext in {"html", "htm"}:
        text = _extract_html_file(path)
        extraction_status = "ok" if text else "empty"

    elif ext in {"png", "jpg", "jpeg", "tiff"}:
        ocr_attempted = True
        try:
            text = ocr_image(path)
            used_ocr = True
            extraction_status = "ok_ocr" if text else "empty"
            if not text:
                failure_reason = "ocr_empty"
        except RuntimeError as exc:
            logger.warning("OCR indisponivel para %s: %s", path, exc)
            extraction_status = "ocr_unavailable"
            failure_reason = "tesseract_missing"
        except Exception as exc:
            logger.warning("OCR falhou para %s: %s", path, exc)
            extraction_status = "ocr_fail"
            failure_reason = type(exc).__name__

    elif ext == "txt":
        text = _read_text_safe(path)
        extraction_status = "ok" if text else "empty"

    else:
        text = _read_text_safe(path)
        extraction_status = "ok" if text else "empty"

    out_dir.mkdir(parents=True, exist_ok=True)
    ocr_dir.mkdir(parents=True, exist_ok=True)

    txt_path = out_dir / f"{path.stem}.txt"
    txt_path.write_text(text or "", encoding="utf-8")

    if used_ocr:
        (ocr_dir / f"{path.stem}.txt").write_text(text or "", encoding="utf-8")

    return {
        "file": str(path),
        "ext": ext,
        "used_ocr": used_ocr,
        "ocr_attempted": ocr_attempted,
        "ocr_failed_pages": ";".join(map(str, ocr_failed_pages)),
        "text_path": str(txt_path),
        "chars": len(text or ""),
        "extraction_status": extraction_status,
        "failure_reason": failure_reason,
    }
