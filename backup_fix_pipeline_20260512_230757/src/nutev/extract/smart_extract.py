from __future__ import annotations
from pathlib import Path
from nutev.extract.pdf_text import extract_pdf_text, ocr_scanned_pdf
from nutev.extract.docx_text import extract_docx_text
from nutev.extract.spreadsheet_text import extract_csv_text, extract_sheet_text
from nutev.extract.html_text import extract_html_text
from nutev.extract.image_ocr import ocr_image

def extract_document(path: Path, ocr_dir: Path, out_dir: Path, logger) -> dict:
    ext = path.suffix.lower().lstrip(".")
    text, used_ocr, ocr_failed_pages = "", False, []
    if ext == "pdf":
        text, has_native = extract_pdf_text(path)
        if not has_native:
            text, ocr_failed_pages = ocr_scanned_pdf(path, logger)
            used_ocr = True
    elif ext == "docx": text = extract_docx_text(path)
    elif ext in {"xlsx","xls"}: text, _ = extract_sheet_text(path)
    elif ext == "csv": text, _ = extract_csv_text(path)
    elif ext in {"html","htm"}:
        payload = extract_html_text(path.read_text(encoding="utf-8", errors="ignore"))
        text = "\n".join([payload.get("title",""), *payload.get("headings", []), payload.get("body","")])
    elif ext in {"png","jpg","jpeg","tiff"}:
        try: text = ocr_image(path); used_ocr = True
        except Exception as e: logger.warning("OCR falhou para %s: %s", path, e)
    elif ext == "txt": text = path.read_text(encoding="utf-8", errors="ignore")
    out_dir.mkdir(parents=True, exist_ok=True); ocr_dir.mkdir(parents=True, exist_ok=True)
    txt_path = out_dir / f"{path.stem}.txt"; txt_path.write_text(text or "", encoding="utf-8")
    if used_ocr: (ocr_dir / f"{path.stem}.txt").write_text(text or "", encoding="utf-8")
    return {"file": str(path), "ext": ext, "used_ocr": used_ocr, "ocr_failed_pages": ";".join(map(str, ocr_failed_pages)), "text_path": str(txt_path), "chars": len(text or ""), "extraction_status": "ok" if text else "empty"}
