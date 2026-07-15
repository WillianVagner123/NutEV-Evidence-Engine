"""P2.1 — tests for the official-guide fetcher (mocked network)."""
from __future__ import annotations

from pathlib import Path

from nutev.acquire.guias_fetcher import fetch_guide, fetch_guides, load_guide_sources

CONFIG = Path(__file__).resolve().parents[1] / "config"


class _Resp:
    def __init__(self, content=b"", code=200, ctype=""):
        self.content, self.status_code = content, code
        self.headers = {"Content-Type": ctype}


class _Session:
    def __init__(self, mapping):
        self.mapping = mapping  # url -> _Resp

    def get(self, url, timeout=None):
        return self.mapping.get(url, _Resp(code=404))


def test_load_guide_sources_from_manifest():
    sources = load_guide_sources(CONFIG)
    assert sources and all("url" in s for s in sources)
    # The FAO/WHO global entries are present.
    joined = " ".join(s.get("institution", "") + s.get("name", "") for s in sources).lower()
    assert "fao" in joined or "world health" in joined


def test_fetch_guide_pdf_records_provenance(tmp_path: Path):
    url = "https://example.org/guide.pdf"
    session = _Session({url: _Resp(content=b"%PDF-1.4 body", ctype="application/pdf")})
    src = {"name": "Brazil FBDG", "country": "Brazil", "institution": "Ministry of Health", "url": url, "authority": 1}
    rec = fetch_guide(src, tmp_path, session)
    assert rec["fulltext_status"] == "fulltext_pdf"
    assert rec["sha256"] and len(rec["sha256"]) == 64
    assert rec["source_url"] == url and rec["access_date"].endswith("+00:00")
    assert Path(rec["archived_pdf_path"]).exists()
    assert rec["aacods_authority_tier"] == 1


def test_fetch_guide_http_error_is_non_fatal(tmp_path: Path):
    session = _Session({})  # everything 404
    rec = fetch_guide({"name": "X", "url": "https://dead/guide"}, tmp_path, session)
    assert rec["fulltext_status"] == "error"
    assert rec["reason"] == "http_404"
    assert rec["archived_pdf_path"] == ""


def test_fetch_guides_batch_and_limit(tmp_path: Path):
    urls = {f"https://x/{i}.pdf": _Resp(content=b"%PDF-1.4", ctype="application/pdf") for i in range(3)}
    session = _Session(urls)
    sources = [{"name": f"g{i}", "url": u} for i, u in enumerate(urls)]
    recs = fetch_guides(sources, tmp_path, session, limit=2)
    assert len(recs) == 2
