"""End-to-end test for the guides pipeline (fetch -> extract -> code -> phrases).

Uses a mocked HTTP session that returns HTML guides so extraction runs without
tesseract/OCR, and a minimal settings stub.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from nutev.pipelines.guides_pipeline import process_guide, run_guides

_LOG = logging.getLogger("test")

_GUIDE_HTML = (
    "<html><body><h1>National Dietary Guideline</h1>"
    "<p>This national dietary guideline recommends increasing fruit and vegetable "
    "intake and choosing whole grains to improve overall diet quality across the "
    "population. It advises reducing saturated fat, sodium and sugar intake, and "
    "limiting ultra-processed foods in everyday meals. Families should share meals "
    "together whenever possible to strengthen commensality and food culture, which "
    "supports a healthier eating environment at home. Health services must improve "
    "adherence and reduce the barriers to implementation of these recommendations "
    "in primary care settings. Cooking skills and meal planning are actively "
    "encouraged to build better food literacy, including reading food labels and "
    "preparing balanced meals on a limited budget. These strategies aim to make "
    "healthy eating feasible, acceptable and sustainable for all households.</p>"
    "</body></html>"
).encode("utf-8")


class _Resp:
    def __init__(self, content=b"", code=200, ctype="text/html"):
        self.content, self.status_code = content, code
        self.headers = {"Content-Type": ctype}


class _Session:
    def __init__(self, mapping):
        self.mapping = mapping

    def get(self, url, timeout=None):
        return self.mapping.get(url, _Resp(code=404))


class _Settings:
    """Minimal settings stub with the output dirs the pipeline touches."""

    def __init__(self, root: Path):
        self.config_root = Path(__file__).resolve().parents[1] / "config"
        self.output_dirs = {
            k: root / k
            for k in ("03C_official_docs", "04_ocr_text", "05_extraction", "06_tables", "07_logs", "10_curated")
        }
        for d in self.output_dirs.values():
            d.mkdir(parents=True, exist_ok=True)


def test_process_guide_codes_and_extracts_phrases(tmp_path: Path):
    settings = _Settings(tmp_path)
    # Save an HTML guide to disk and build its provenance record.
    guide = settings.output_dirs["03C_official_docs"] / "brazil__guide.html"
    guide.write_bytes(_GUIDE_HTML)
    record = {
        "name": "Brazil FBDG", "country": "Brazil", "institution": "Ministry of Health",
        "source_url": "https://x/guide", "fulltext_status": "fulltext_html",
        "archived_pdf_path": str(guide),
    }
    row = process_guide(record, settings, _LOG)
    assert row["extraction_status"] == "fake_pdf_html" or row["extraction_status"] == "ok"
    # A/B/C/D coding present; at least one domain flagged for a guideline.
    assert row["n_domains"] >= 1
    # Key phrases extracted, with the domain-tagged readable block incl. page.
    assert row["n_key_phrases"] >= 1
    assert "[" in row["key_phrases_text"] and "(p." in row["key_phrases_text"]
    # Every key phrase carries the reference + page — the source, not just text.
    first = row["key_phrases"][0]
    assert first["page"] >= 1
    assert first["reference"] == row["reference"]
    assert "Ministry of Health" in row["reference"]
    assert "Brazil" in row["reference"]


def test_run_guides_offline_processes_local_files(tmp_path: Path):
    settings = _Settings(tmp_path)
    (settings.output_dirs["03C_official_docs"] / "g1.html").write_bytes(_GUIDE_HTML)
    (settings.output_dirs["03C_official_docs"] / "g2.html").write_bytes(_GUIDE_HTML)

    summary = run_guides(settings, _LOG, session=None)
    assert summary["guides_processed"] == 2
    assert summary["guides_with_fulltext"] == 2
    assert summary["key_phrases_total"] >= 2
    # Table + detail JSON written.
    assert (settings.output_dirs["06_tables"] / "NUTEV_GUIDES_CODED.csv").exists()
    detail = json.loads((settings.output_dirs["10_curated"] / "guides_coded.json").read_text())
    assert len(detail) == 2 and "key_phrases" in detail[0]


def test_run_guides_with_mocked_session_fetches_then_codes(tmp_path: Path):
    settings = _Settings(tmp_path)
    # Point the first two manifest guides at our mocked HTML.
    from nutev.acquire.guias_fetcher import load_guide_sources

    sources = load_guide_sources(settings.config_root)
    urls = {s["url"]: _Resp(content=_GUIDE_HTML) for s in sources[:2] if s.get("url")}
    session = _Session(urls)

    summary = run_guides(settings, _LOG, session=session, limit=2)
    assert summary["guides_processed"] == 2
    # At least one guide fetched as HTML and coded with key phrases.
    assert summary["guides_with_fulltext"] >= 1
    assert summary["key_phrases_total"] >= 1
