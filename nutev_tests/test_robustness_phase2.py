"""Phase 2 robustness: page cap, resilient render, download cap, resume-after-crash."""
from __future__ import annotations

import logging
from pathlib import Path

import nutev.extract.pdf_text as pdf_text
from nutev.acquire.guias_fetcher import fetch_guide

_LOG = logging.getLogger("test")


def test_ocr_page_cap_stops_early(monkeypatch, tmp_path):
    p = tmp_path / "big.pdf"
    p.write_bytes(b"%PDF-1.4 fake")
    monkeypatch.setattr(pdf_text, "is_probably_pdf_file", lambda _p: True)

    def many_pages(path, dpi=300):
        for _ in range(100):
            yield object()

    monkeypatch.setattr(pdf_text, "_render_pdf_pages", many_pages)
    monkeypatch.setattr(pdf_text, "ocr_pil_image", lambda img: "diet quality guideline text page")
    monkeypatch.setenv("NUTEV_OCR_MAX_PAGES", "3")

    pages, _failed = pdf_text._ocr_pages_at_dpi(p, 300, _LOG)
    assert len(pages) == 3  # capped


def test_render_error_on_one_page_is_skipped(monkeypatch, tmp_path):
    p = tmp_path / "scan.pdf"
    p.write_bytes(b"%PDF-1.4 fake")
    monkeypatch.setattr(pdf_text, "is_probably_pdf_file", lambda _p: True)

    def flaky_pages(path, dpi=300):
        yield "img1"
        raise ValueError("corrupt page 2")

    monkeypatch.setattr(pdf_text, "_render_pdf_pages", flaky_pages)
    monkeypatch.setattr(pdf_text, "ocr_pil_image", lambda img: "good page one about diet quality")
    monkeypatch.delenv("NUTEV_OCR_MAX_PAGES", raising=False)

    pages, failed = pdf_text._ocr_pages_at_dpi(p, 300, _LOG)
    assert pages[0].startswith("good page one")  # page 1 kept
    assert 2 in failed                            # page 2 skipped, recorded


def test_first_page_render_failure_propagates(monkeypatch, tmp_path):
    p = tmp_path / "norender.pdf"
    p.write_bytes(b"%PDF-1.4 fake")

    def no_renderer(path, dpi=300):
        raise ImportError("no PDF renderer")
        yield  # pragma: no cover

    monkeypatch.setattr(pdf_text, "_render_pdf_pages", no_renderer)
    monkeypatch.delenv("NUTEV_OCR_MAX_PAGES", raising=False)
    # A first-page failure must propagate (so the caller can flag OCR-setup).
    try:
        pdf_text._ocr_pages_at_dpi(p, 300, _LOG)
    except ImportError:
        pass
    else:
        raise AssertionError("expected the first-page render failure to propagate")


class _Resp:
    def __init__(self, content=b"", code=200, ctype="application/pdf"):
        self.content, self.status_code = content, code
        self.headers = {"Content-Type": ctype}


class _Session:
    def __init__(self, resp):
        self._resp = resp

    def get(self, url, timeout=None):
        return self._resp


def test_download_size_cap_rejects_huge_file(monkeypatch, tmp_path):
    monkeypatch.setenv("NUTEV_MAX_DOWNLOAD_MB", "0.001")  # ~1 KB cap
    big = b"%PDF-1.4 " + b"x" * 5000
    rec = fetch_guide({"name": "big", "url": "https://x/big.pdf"}, tmp_path, _Session(_Resp(big)))
    assert rec["fulltext_status"] == "error"
    assert rec["reason"].startswith("too_large_")


def test_download_under_cap_ok(monkeypatch, tmp_path):
    monkeypatch.setenv("NUTEV_MAX_DOWNLOAD_MB", "10")
    rec = fetch_guide({"name": "ok", "url": "https://x/ok.pdf"}, tmp_path, _Session(_Resp(b"%PDF-1.4 body")))
    assert rec["fulltext_status"] == "fulltext_pdf"


def test_resume_after_crash_no_duplication(tmp_path, monkeypatch):
    # A run that crashes midway still checkpoints finished guides; the re-run
    # completes the rest with no duplication.
    import nutev.pipelines.guides_pipeline as gp

    html = b"<html><body><h1>G</h1><p>" + b"This dietary guideline recommends fruit and vegetables and whole grains for diet quality. " * 6 + b"</p></body></html>"

    class _Settings:
        def __init__(self, root: Path):
            self.config_root = Path(__file__).resolve().parents[1] / "config"
            self.output_dirs = {
                k: root / k
                for k in ("03C_official_docs", "04_ocr_text", "05_extraction", "06_tables", "07_logs", "10_curated")
            }
            for d in self.output_dirs.values():
                d.mkdir(parents=True, exist_ok=True)

    settings = _Settings(tmp_path)
    for i in range(4):
        (settings.output_dirs["03C_official_docs"] / f"g{i}.html").write_bytes(html)

    real_process = gp.process_guide
    calls = {"n": 0}

    def crashing_process(record, s, logger):
        calls["n"] += 1
        if calls["n"] == 3:  # crash on the 3rd guide the first time around
            raise RuntimeError("boom")
        return real_process(record, s, logger)

    monkeypatch.setattr(gp, "process_guide", crashing_process)
    try:
        gp.run_guides(settings, _LOG, session=None, workers=1)
    except RuntimeError:
        pass
    checkpoint = settings.output_dirs["07_logs"] / "guides_checkpoint.jsonl"
    done_after_crash = len(checkpoint.read_text().splitlines())
    assert 0 < done_after_crash < 4  # some, not all, were saved

    # Re-run without the crash: completes the rest, no duplicates in the checkpoint.
    monkeypatch.setattr(gp, "process_guide", real_process)
    summary = gp.run_guides(settings, _LOG, session=None, workers=1)
    assert summary["guides_processed"] == 4
    keys = [line for line in checkpoint.read_text().splitlines() if line.strip()]
    import json
    seen = [json.loads(k)["_guide_key"] for k in keys]
    assert len(seen) == len(set(seen)) == 4  # every guide exactly once
