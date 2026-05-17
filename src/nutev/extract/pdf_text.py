from __future__ import annotations

from pathlib import Path

from nutev.extract.image_ocr import is_tesseract_available, ocr_pil_image


def is_probably_pdf_file(path: Path) -> bool:
    try:
        header = path.read_bytes()[:8]
        return header.startswith(b"%PDF-")
    except Exception:
        return False


def extract_pdf_text(path: Path) -> tuple[str, bool]:
    if not is_probably_pdf_file(path):
        return "", False

    try:
        import pypdf

        reader = pypdf.PdfReader(str(path), strict=False)
        txt = "\n".join((page.extract_text() or "") for page in reader.pages).strip()
        return txt, bool(txt)
    except Exception:
        return "", False


def is_usable_pdf_text(text: str) -> bool:
    cleaned = " ".join((text or "").split())
    if len(cleaned) < 120:
        return False

    non_space_chars = [char for char in cleaned if not char.isspace()]
    if not non_space_chars:
        return False

    alpha_chars = sum(char.isalpha() for char in non_space_chars)
    return (alpha_chars / len(non_space_chars)) >= 0.2


def should_run_ocr_fallback(text: str) -> bool:
    return not is_usable_pdf_text(text)


def ocr_scanned_pdf(path: Path, logger) -> tuple[str, list[int], str | None]:
    failed_pages: list[int] = []
    texts: list[str] = []

    if not is_probably_pdf_file(path):
        return "", [0], "not_pdf"

    if not is_tesseract_available():
        logger.warning("OCR indisponivel para %s: tesseract ausente", path)
        return "", [], "tesseract_missing"

    try:
        from pdf2image import convert_from_path

        pages = convert_from_path(str(path), dpi=300)
    except Exception as exc:
        logger.warning("Falha convert_from_path %s: %s", path, exc)
        return "", [0], "pdf_render_failed"

    if not pages:
        return "", [0], "no_pages_rendered"

    for page_number, image in enumerate(pages, start=1):
        try:
            page_text = ocr_pil_image(image).strip()
        except Exception as exc:
            logger.warning("Falha OCR page=%s file=%s erro=%s", page_number, path, exc)
            failed_pages.append(page_number)
            continue

        if page_text:
            texts.append(page_text)
        else:
            failed_pages.append(page_number)

    if texts:
        return "\n".join(texts), failed_pages, None

    return "", failed_pages, "ocr_empty"
