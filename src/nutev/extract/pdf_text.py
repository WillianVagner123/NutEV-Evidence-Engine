from __future__ import annotations

import shutil
from pathlib import Path
from nutev.extract.image_ocr import ocr_pil_image


def _has_pymupdf() -> bool:
    """Whether PyMuPDF (fitz) is importable — a pip-only alternative to poppler."""
    try:
        import fitz  # noqa: F401  (PyMuPDF)

        return True
    except Exception:
        return False


def _has_poppler() -> bool:
    return shutil.which("pdftoppm") is not None or shutil.which("pdftocairo") is not None


def missing_ocr_dependencies() -> list[str]:
    """Return human-readable names of OCR prerequisites that are unavailable.

    Scanned/image-only PDFs need two capabilities: rendering the page to an
    image, and reading text from that image (OCR).

    - Rendering works with **PyMuPDF** (``pip install pymupdf`` — no system
      program needed) OR with ``pdf2image`` + the system ``poppler``. Only when
      *neither* path is available do we ask the user to install something.
    - OCR needs ``pytesseract`` (pip) plus the ``tesseract`` system program.

    When any are missing, extraction silently yields no text; this lets the
    pipeline report *why* and tell the user exactly what to install instead of
    masking it as an empty PDF.
    """
    missing: list[str] = []
    # Rendering: satisfied by PyMuPDF alone, or by pdf2image + poppler.
    try:
        import pdf2image  # noqa: F401

        has_pdf2image = True
    except Exception:
        has_pdf2image = False
    if not _has_pymupdf() and not (has_pdf2image and _has_poppler()):
        missing.append('PDF rendering: pip install pymupdf (no system install), OR pdf2image + poppler')
    # OCR engine.
    try:
        import pytesseract  # noqa: F401
    except Exception:
        missing.append('pytesseract (pip install -e ".[documents]")')
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


def _render_pdf_pages(path: Path):
    """Render PDF pages to PIL images. Prefer PyMuPDF (pip-only, no poppler).

    Returns an iterable of PIL Images, or raises if no renderer is available.
    """
    if _has_pymupdf():
        import fitz  # PyMuPDF
        from PIL import Image

        images = []
        with fitz.open(str(path)) as doc:
            for page in doc:
                # 200 DPI is a good balance of OCR accuracy and speed.
                pix = page.get_pixmap(dpi=200)
                images.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
        return images
    # Fallback: pdf2image needs the system poppler binaries.
    from pdf2image import convert_from_path

    return convert_from_path(str(path))


def ocr_scanned_pdf(path: Path, logger) -> tuple[str, list[int]]:
    failed = []
    texts = []

    if not is_probably_pdf_file(path):
        return "", [0]

    try:
        pages = _render_pdf_pages(path)
    except Exception as e:
        logger.warning("Falha ao renderizar PDF para OCR %s: %s", path, e)
        return "", [0]

    for i, img in enumerate(pages, start=1):
        try:
            texts.append(ocr_pil_image(img))
        except Exception:
            failed.append(i)

    return "\n".join(texts), failed