from __future__ import annotations
from pathlib import Path

def ocr_image(path: Path) -> str:
    import pytesseract
    from PIL import Image
    return pytesseract.image_to_string(Image.open(path))

def ocr_pil_image(image) -> str:
    import pytesseract
    return pytesseract.image_to_string(image)
