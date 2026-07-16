"""OCR for images and rendered PDF pages.

The previous implementation ran ``pytesseract.image_to_string`` with the default
English model, no image preparation and no engine config — which is why OCR of
non-English national guides (Portuguese, Spanish, French, …) came out poor. This
version:

- OCRs with a **multilingual** model set (default ``por+eng+spa``, overridable via
  ``NUTEV_OCR_LANG``) and falls back to English if a language pack is missing;
- **prepares the image** (grayscale + autocontrast + upscales low-resolution
  pages) so tesseract has clean, large glyphs to read;
- passes a sensible engine config (LSTM engine, automatic page segmentation,
  preserved inter-word spaces), overridable via ``NUTEV_OCR_CONFIG``.

Everything is best-effort and dependency-light (PIL only). Language packs must be
installed in the system tesseract (e.g. ``tesseract-ocr-por``); when they are
not, we degrade to English instead of failing.
"""
from __future__ import annotations

import os
from pathlib import Path

# Default to Portuguese + English + Spanish (the bulk of the guide corpus).
# Override with e.g. NUTEV_OCR_LANG="por+eng+spa+fra+ita".
_DEFAULT_LANG = os.environ.get("NUTEV_OCR_LANG", "por+eng+spa")
# LSTM engine (oem 1), automatic page segmentation (psm 3), keep word spacing.
_DEFAULT_CONFIG = os.environ.get("NUTEV_OCR_CONFIG", "--oem 1 --psm 3 -c preserve_interword_spaces=1")

# Below this longest-side pixel count an image is upscaled before OCR — small
# renders/scans lose glyph detail that tesseract needs.
_MIN_LONG_SIDE = 1800


def _preprocess(image):
    """Grayscale + autocontrast + upscale a PIL image for cleaner OCR."""
    from PIL import Image, ImageOps

    img = image.convert("L")            # grayscale
    img = ImageOps.autocontrast(img)    # normalize contrast
    w, h = img.size
    longest = max(w, h)
    if longest and longest < _MIN_LONG_SIDE:
        scale = _MIN_LONG_SIDE / longest
        img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
    return img


def ocr_pil_image(image, *, lang: str | None = None, config: str | None = None) -> str:
    """OCR a PIL image with preprocessing, multilingual model and engine config.

    Falls back to English if the requested language pack is not installed; if
    tesseract itself is unavailable the underlying error propagates so the caller
    can record the page as failed.
    """
    import pytesseract

    lang = lang or _DEFAULT_LANG
    config = _DEFAULT_CONFIG if config is None else config
    prepared = _preprocess(image)
    try:
        return pytesseract.image_to_string(prepared, lang=lang, config=config)
    except pytesseract.TesseractError:
        # A missing language pack raises TesseractError — degrade to English
        # rather than losing the page entirely.
        return pytesseract.image_to_string(prepared, lang="eng", config=config)


def ocr_image(path: Path, *, lang: str | None = None, config: str | None = None) -> str:
    """OCR a standalone image file through the same improved path."""
    from PIL import Image

    with Image.open(path) as img:
        return ocr_pil_image(img, lang=lang, config=config)
