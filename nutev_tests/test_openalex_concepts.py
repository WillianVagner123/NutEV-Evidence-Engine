from __future__ import annotations

import json

from nutev.search import openalex, openalex_concepts


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.url = "https://api.openalex.org/concepts"

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def _concepts_payload(concept_url):
    return {"results": [{"id": concept_url, "display_name": "Diabetes mellitus"}]}


def test_resolve_concept_id_parses_trailing_id_and_writes_cache(tmp_path, monkeypatch):
    captured = {}

    def fake_get(url, **kwargs):
        captured["url"] = url
        captured["params"] = kwargs.get("params")
        return FakeResponse(_concepts_payload("https://openalex.org/C71924100"))

    monkeypatch.setattr(openalex_concepts.requests, "get", fake_get)
    monkeypatch.delenv("NUTEV_DISABLE_NETWORK", raising=False)

    concept_id = openalex_concepts.resolve_concept_id("diabetes", config_root=tmp_path)

    assert concept_id == "C71924100"
    assert captured["url"] == "https://api.openalex.org/concepts"
    assert captured["params"]["search"] == "diabetes"
    assert captured["params"]["per-page"] == 1

    cache_file = tmp_path / "openalex_concepts.json"
    assert cache_file.exists()
    on_disk = json.loads(cache_file.read_text(encoding="utf-8"))
    assert on_disk["diabetes"] == "C71924100"


def test_resolve_concept_id_no_result_caches_empty_sentinel(tmp_path, monkeypatch):
    monkeypatch.setattr(
        openalex_concepts.requests, "get", lambda url, **kw: FakeResponse({"results": []})
    )
    monkeypatch.delenv("NUTEV_DISABLE_NETWORK", raising=False)

    concept_id = openalex_concepts.resolve_concept_id("zzz-nope", config_root=tmp_path)

    assert concept_id is None
    on_disk = json.loads((tmp_path / "openalex_concepts.json").read_text(encoding="utf-8"))
    assert on_disk["zzz-nope"] == ""


def test_cache_hit_does_not_call_network(tmp_path, monkeypatch):
    cache_file = tmp_path / "openalex_concepts.json"
    cache_file.write_text(json.dumps({"diabetes": "C71924100"}), encoding="utf-8")

    def boom(*args, **kwargs):
        raise AssertionError("network must not be called on a cache hit")

    monkeypatch.setattr(openalex_concepts.requests, "get", boom)
    monkeypatch.delenv("NUTEV_DISABLE_NETWORK", raising=False)

    # Case-insensitive / whitespace-insensitive key normalisation.
    assert openalex_concepts.resolve_concept_id("  Diabetes  ", config_root=tmp_path) == "C71924100"


def test_disable_network_returns_cached_value_without_network(tmp_path, monkeypatch):
    cache_file = tmp_path / "openalex_concepts.json"
    cache_file.write_text(json.dumps({"diabetes": "C71924100"}), encoding="utf-8")

    def boom(*args, **kwargs):
        raise AssertionError("network must not be called when disabled")

    monkeypatch.setattr(openalex_concepts.requests, "get", boom)
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")

    assert openalex_concepts.resolve_concept_id("diabetes", config_root=tmp_path) == "C71924100"
    # Unknown term -> None, still no network.
    assert openalex_concepts.resolve_concept_id("unknown-term", config_root=tmp_path) is None


def test_resolve_concept_ids_dedupes_and_drops_none(tmp_path, monkeypatch):
    monkeypatch.delenv("NUTEV_DISABLE_NETWORK", raising=False)

    lookup = {
        "diabetes": "https://openalex.org/C71924100",
        "obesity": "https://openalex.org/C2779134260",
        # "nutrition" intentionally maps to no concept -> dropped.
    }

    def fake_get(url, **kwargs):
        term = kwargs.get("params", {}).get("search")
        concept_url = lookup.get(term)
        if concept_url:
            return FakeResponse({"results": [{"id": concept_url}]})
        return FakeResponse({"results": []})

    monkeypatch.setattr(openalex_concepts.requests, "get", fake_get)

    ids = openalex_concepts.resolve_concept_ids(
        ["diabetes", "Diabetes", "obesity", "nutrition"], config_root=tmp_path
    )

    # Duplicate "diabetes"/"Diabetes" collapses; "nutrition" (None) dropped.
    assert ids == ["C71924100", "C2779134260"]


def test_resolve_concept_ids_empty_input(tmp_path):
    assert openalex_concepts.resolve_concept_ids([], config_root=tmp_path) == []


# --- search_openalex concept_filter wiring -------------------------------


class FakeWorksResponse:
    def __init__(self):
        self.url = "https://api.openalex.org/works"

    def json(self):
        return {"results": []}

    def raise_for_status(self):
        return None


def test_search_openalex_includes_concept_filter(monkeypatch):
    captured = {}

    def fake_get(url, **kwargs):
        captured["url"] = url
        captured["params"] = kwargs.get("params")
        return FakeWorksResponse()

    monkeypatch.setattr(openalex.requests, "get", fake_get)
    monkeypatch.delenv("NUTEV_DISABLE_NETWORK", raising=False)

    openalex.search_openalex("diet", per_page=5, concept_filter="C123|C456")

    assert "filter" in captured["params"]
    assert "concepts.id:C123" in captured["params"]["filter"]
    assert captured["params"]["filter"] == "concepts.id:C123|C456"


def test_search_openalex_without_concept_filter_has_no_concepts_id(monkeypatch):
    captured = {}

    def fake_get(url, **kwargs):
        captured["params"] = kwargs.get("params")
        return FakeWorksResponse()

    monkeypatch.setattr(openalex.requests, "get", fake_get)
    monkeypatch.delenv("NUTEV_DISABLE_NETWORK", raising=False)

    openalex.search_openalex("diet", per_page=5)

    # Backward compatible: no filter key, no concepts.id anywhere.
    assert "filter" not in captured["params"]
    assert "concepts.id" not in json.dumps(captured["params"])
