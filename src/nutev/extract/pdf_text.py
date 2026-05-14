from __future__ import annotations

from pathlib import Path
from nutev.extract.image_ocr import ocr_pil_image


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