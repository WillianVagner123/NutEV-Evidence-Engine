from __future__ import annotations

import shutil
from pathlib import Path


def is_tesseract_available() -> bool:
    return shutil.which("tesseract") is not None


def _require_tesseract() -> None:
    if not is_tesseract_available():
        raise RuntimeError("tesseract binary not available")


def ocr_image(path: Path) -> str:
    import pytesseract
    from PIL import Image

    _require_tesseract()
    return pytesseract.image_to_string(Image.open(path))


def ocr_pil_image(image) -> str:
    import pytesseract

    _require_tesseract()
    return pytesseract.image_to_string(image)
