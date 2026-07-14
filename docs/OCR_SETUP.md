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

## 1. Python packages (the `documents` extra)

```bash
pip install -e ".[documents]"
```

The Windows launcher (`Iniciar-NutEV-Windows.bat`) already installs this for
you on first run.

## 2. System programs

| Program    | Used for                         | Windows | macOS | Linux (Debian/Ubuntu) |
|------------|----------------------------------|---------|-------|-----------------------|
| poppler    | turning PDF pages into images    | download a poppler build and add its `bin` folder to `PATH` | `brew install poppler` | `sudo apt install poppler-utils` |
| tesseract  | reading text from those images   | install the tesseract Windows build and add it to `PATH` | `brew install tesseract` | `sudo apt install tesseract-ocr` |

### Windows, step by step

1. **poppler** — download a Windows build (e.g. the "poppler-windows" release),
   unzip it (for example to `C:\poppler`), then add `C:\poppler\Library\bin`
   to your `PATH` (Windows Search → "Edit the system environment variables" →
   *Environment Variables* → edit `Path` → *New*).
2. **tesseract** — install the tesseract Windows build (UB Mannheim build is
   common), keeping the default option that adds it to `PATH`.
3. Close and reopen VS Code / the terminal so the new `PATH` takes effect.

## 3. Check it worked

```bash
pdftoppm -h
tesseract --version
```

If both print output, OCR is ready. Re-run NutEV and the
`extraction_pdf_needs_ocr_setup` count in `run_summary.json` should drop to `0`
for scanned PDFs that can now be read.

> Note: OCR reads what is printed on the page. It does **not** validate the
> science. Extracted claims still carry `claim_status` (`supported` =
> quote-backed, `inference_only` = not quote-backed) and always require human
> review — see `docs/AI_USE_AND_HUMAN_OVERSIGHT.md`.
