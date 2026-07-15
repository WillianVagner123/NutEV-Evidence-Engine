"""Tests for the official-source verifier (`nutev verify-sources`)."""
from __future__ import annotations

from pathlib import Path

from nutev.search.verify_sources import verify_official_sources, write_verification_report

CONFIG = Path(__file__).resolve().parents[1] / "config"


class _Resp:
    def __init__(self, code: int):
        self.status_code = code

    def close(self):
        pass


class _Session:
    """Return a status by host substring to simulate live/dead/blocked URLs."""

    def __init__(self, mapping: dict[str, int], default: int = 200):
        self.mapping = mapping
        self.default = default

    def get(self, url, **kwargs):
        for needle, code in self.mapping.items():
            if needle in url:
                if code == 0:
                    raise OSError("name resolution failed")
                return _Resp(code)
        return _Resp(self.default)


def test_verify_classifies_live_dead_blocked():
    session = _Session({"who.int": 200, "fao.org": 404, "dietaryguidelines.gov": 403})
    rows = verify_official_sources(CONFIG, timeout=5, session=session)
    by_url = {r["url"]: r for r in rows}
    who = next(r for u, r in by_url.items() if "who.int" in u)
    fao = next(r for u, r in by_url.items() if "food-dietary-guidelines/en" in u)
    dga = next(r for u, r in by_url.items() if "dietaryguidelines.gov" in u)
    assert who["ok"] and who["reason"] == "ok"
    assert not fao["ok"] and fao["status_code"] == 404
    assert dga["ok"] and dga["reason"] == "blocked_but_exists"  # 403 -> exists


def test_verify_respects_network_disabled(monkeypatch):
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")
    rows = verify_official_sources(CONFIG, timeout=5)
    assert rows and all(r["reason"] == "network_disabled" for r in rows)


def test_write_verification_report(tmp_path: Path):
    session = _Session({}, default=200)
    rows = verify_official_sources(CONFIG, timeout=5, session=session)
    out = write_verification_report(rows, tmp_path / "report.csv")
    assert out.exists()
    content = out.read_text(encoding="utf-8-sig")
    assert "status_code" in content and "url" in content
    assert len(rows) >= 50
