# Reading PDFs (OCR) — setup guide

NutEV reads text from the documents it downloads. Most PDFs contain an
embedded text layer and are read with no extra setup. **Scanned / image-only
PDFs** (a photo of a page, with no text layer) can only be read with OCR, which
needs two system programs in addition to the Python packages.

If OCR is not configured, NutEV does **not** crash and does **not** silently
pretend the document was read. It:

- logs one clear warning naming exactly what to install, and
- marks those documents with `extraction_status = pdf_needs_ocr_setup`,
  counted in `07_logs/run_summary.json` as `extraction_pdf_needs_ocr_setup`.

Scanned-PDF OCR needs two things: (a) **render** each page to an image, and
(b) **read** the text from that image. There are two ways to get (a).

## 1. Python packages (the `documents` extra)

```bash
pip install -e ".[documents]"
```

This installs **PyMuPDF** (`pymupdf`), which renders PDF pages to images
**without any system program** — so you do NOT need poppler. The Windows
launcher (`Iniciar-NutEV-Windows.bat`) installs this for you on first run.

## 2. The OCR engine: `tesseract`

`tesseract` is the one system program you still need (it does the actual
text-reading). It is small and adds itself to `PATH`.

| OS | Install |
|----|---------|
| Windows | install the tesseract Windows build (the UB Mannheim build is common), keeping the default "add to PATH" option |
| macOS | `brew install tesseract` |
| Linux (Debian/Ubuntu) | `sudo apt install tesseract-ocr` |

Then close and reopen VS Code / the terminal so the new `PATH` takes effect.

> **poppler is optional.** With PyMuPDF installed you can skip it entirely. It
> is only used as a fallback if PyMuPDF is not available; if you prefer it,
> install a poppler build and add its `bin` folder to `PATH`.

## 3. Check it worked

```bash
tesseract --version
python -c "import fitz; print('pymupdf ok')"
```

If both print output, OCR is ready. Re-run NutEV and the
`extraction_pdf_needs_ocr_setup` count in `run_summary.json` should drop to `0`
for scanned PDFs that can now be read.

> Note: OCR reads what is printed on the page. It does **not** validate the
> science. Extracted claims still carry `claim_status` (`supported` =
> quote-backed, `inference_only` = not quote-backed) and always require human
> review — see `docs/AI_USE_AND_HUMAN_OVERSIGHT.md`.
