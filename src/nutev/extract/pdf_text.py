from __future__ import annotations

import shutil
from pathlib import Path
from nutev.extract.image_ocr import ocr_pil_image


def missing_ocr_dependencies() -> list[str]:
    """Return human-readable names of OCR prerequisites that are unavailable.

    Scanned/image-only PDFs can only be read when both the Python packages
    (installed via the ``documents`` extra) and the system binaries (poppler for
    pdf2image, tesseract for OCR) are present. When any are missing, extraction
    silently yields no text; this lets the pipeline report *why* and tell the
    user exactly what to install instead of masking it as an empty PDF.
    """
    missing: list[str] = []
    try:
        import pdf2image  # noqa: F401
    except Exception:
        missing.append('pdf2image (pip install -e ".[documents]")')
    try:
        import pytesseract  # noqa: F401
    except Exception:
        missing.append('pytesseract (pip install -e ".[documents]")')
    if shutil.which("pdftoppm") is None and shutil.which("pdftocairo") is None:
        missing.append("poppler (system package: apt install poppler-utils / brew install poppler / Windows poppler build)")
    if shutil.which("tesseract") is None:
        missing.append("tesseract (system package: apt install tesseract-ocr / brew install tesseract / Windows tesseract build)")
    return missing


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
        txt = "\n".join((p.extract_text() or "") for p in reader.pages).strip()
        return txt, bool(txt)
    except Exception:
        return "", False


def ocr_scanned_pdf(path: Path, logger) -> tuple[str, list[int]]:
    failed = []
    texts = []

    if not is_probably_pdf_file(path):
        return "", [0]

    try:
        from pdf2image import convert_from_path
        pages = convert_from_path(str(path))
    except Exception as e:
        logger.warning("Falha convert_from_path %s: %s", path, e)
        return "", [0]

    for i, img in enumerate(pages, start=1):
        try:
            texts.append(ocr_pil_image(img))
        except Exception:
            failed.append(i)

    return "\n".join(texts), failed