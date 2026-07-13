from __future__ import annotations

from pathlib import Path
from nutev.extract.pdf_text import extract_pdf_text, ocr_scanned_pdf, is_probably_pdf_file
from nutev.extract.docx_text import extract_docx_text
from nutev.extract.spreadsheet_text import extract_csv_text, extract_sheet_text
from nutev.extract.html_text import extract_html_text
from nutev.extract.image_ocr import ocr_image


def _read_text_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


# Anti-bot / interstitial / redirect pages that publishers return with HTTP 200
# but which contain no real document. These must NOT be counted as extracted text.
_JUNK_MARKERS = (
    "checking your browser",
    "just a moment",
    "enable javascript",
    "please enable javascript",
    "recaptcha",
    "captcha",
    "verify you are human",
    "are you a robot",
    "attention required",
    "cloudflare",
    "access denied",
    "request has been blocked",
    "ddos protection",
    "security check to access",
    "why have i been blocked",
)

# Minimum characters below which an HTML/text "document" is treated as too thin
# to be a real full text (metadata/landing/redirect stubs).
MIN_MEANINGFUL_CHARS = 400


def looks_like_junk_text(text: str) -> bool:
    """Return True when extracted text is an anti-bot/redirect page or too thin
    to be a real document (e.g. 'Redirecting', 'Checking your browser')."""
    t = (text or "").strip()
    low = t.lower()
    if not t:
        return True
    # Bare redirect/loading stubs.
    if len(t) < 200 and ("redirect" in low or low in {"redirecting", "loading", "loading..."}):
        return True
    # Interstitial/anti-bot pages: a known marker on a short page.
    if len(t) < 3000 and any(marker in low for marker in _JUNK_MARKERS):
        return True
    return False


# Extraction statuses that are only "successful" if the text is real content.
_QUALITY_CHECKED_STATUSES = {"ok", "ok_ocr", "fake_pdf_html", "fake_pdf_text"}


def _raw_contains_junk_markers(path: Path) -> bool:
    """Anti-bot/interstitial pages often carry the marker in raw HTML even when
    readability extracts little visible text."""
    raw = _read_text_safe(path)[:20000].lower()
    return any(marker in raw for marker in _JUNK_MARKERS)


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
    ocr_failed_pages = []
    extraction_status = "empty"

    if ext == "pdf":
        if is_probably_pdf_file(path):
            text, has_native = extract_pdf_text(path)
            if text:
                extraction_status = "ok"
            else:
                ocr_text, ocr_failed_pages = ocr_scanned_pdf(path, logger)
                if ocr_text:
                    text = ocr_text
                    used_ocr = True
                    extraction_status = "ok_ocr"
                else:
                    extraction_status = "pdf_no_text"
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
        try:
            text = ocr_image(path)
            used_ocr = True
            extraction_status = "ok_ocr" if text else "empty"
        except Exception as e:
            logger.warning("OCR falhou para %s: %s", path, e)
            extraction_status = "ocr_fail"

    elif ext == "txt":
        text = _read_text_safe(path)
        extraction_status = "ok" if text else "empty"

    else:
        text = _read_text_safe(path)
        extraction_status = "ok" if text else "empty"

    # Quality gate: reject anti-bot/redirect/interstitial pages and content that
    # is too thin to be a real document. These previously passed as "ok" and
    # polluted the corpus and the extracted-text counts.
    stripped_len = len((text or "").strip())
    is_html_like = ext in {"html", "htm"} or extraction_status == "fake_pdf_html"
    if extraction_status in _QUALITY_CHECKED_STATUSES and looks_like_junk_text(text):
        extraction_status = "junk_or_blocked"
    elif is_html_like and stripped_len < MIN_MEANINGFUL_CHARS and _raw_contains_junk_markers(path):
        # Junk HTML whose visible text extracted thin/empty but whose raw markup
        # is clearly an anti-bot/redirect page.
        extraction_status = "junk_or_blocked"
    elif extraction_status in {"ok", "fake_pdf_html", "fake_pdf_text"} and stripped_len < MIN_MEANINGFUL_CHARS:
        extraction_status = "too_short"

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
        "ocr_failed_pages": ";".join(map(str, ocr_failed_pages)),
        "text_path": str(txt_path),
        "chars": len(text or ""),
        "extraction_status": extraction_status,
    }