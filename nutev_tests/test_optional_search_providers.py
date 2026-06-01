from __future__ import annotations

from nutev.search.brave_optional import search_brave
from nutev.search.google_pse import search_google_pse
from nutev.search.serpapi_optional import search_serpapi


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.url = "https://api.example.test"
    def json(self):
        return self._payload
    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, response):
        self.response = response
    def get(self, *args, **kwargs):
        return self.response
    def close(self):
        pass


def test_google_pse_missing_key_skipped(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_CSE_ID", raising=False)
    result = search_google_pse("nutrition")
    assert result.status == "skipped"


def test_google_pse_mock_success(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "k")
    monkeypatch.setenv("GOOGLE_CSE_ID", "cx")
    monkeypatch.setattr("requests.Session", lambda: FakeSession(FakeResponse({"searchInformation": {"totalResults": "1"}, "items": [{"title": "Doc", "link": "https://example.org", "snippet": "S"}]})))
    result = search_google_pse("nutrition", limit=1)
    assert result.status == "completed"
    assert result.rows[0]["source_provider"] == "google_pse"


def test_serpapi_missing_key_skipped(monkeypatch):
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)
    assert search_serpapi("x").status == "skipped"


def test_brave_missing_key_skipped(monkeypatch):
    monkeypatch.delenv("BRAVE_API_KEY", raising=False)
    assert search_brave("x").status == "skipped"
