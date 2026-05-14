from __future__ import annotations
from pathlib import Path
from nutev.extract.image_ocr import ocr_pil_image

def extract_pdf_text(path: Path) -> tuple[str, bool]:
    try:
        import pypdf
        r = pypdf.PdfReader(str(path))
        txt = "\n".join((p.extract_text() or "") for p in r.pages).strip()
        return txt, bool(txt)
    except Exception:
        return "", False

def ocr_scanned_pdf(path: Path, logger) -> tuple[str, list[int]]:
    failed = []
    texts = []
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
