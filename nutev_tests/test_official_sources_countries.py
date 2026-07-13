"""The global per-country official-source manifest is valid and greatly expands
busca1 official coverage beyond the original handful of sources."""
from __future__ import annotations

import json
from pathlib import Path

from nutev.search.official_sources import manifest_sources

CONFIG = Path(__file__).resolve().parents[1] / "config"


def _load(name: str) -> dict:
    return json.loads((CONFIG / name).read_text(encoding="utf-8"))


def test_countries_manifest_is_valid_and_distinct():
    countries = _load("official_sources_countries.json")
    entries = countries["workstreams"]["busca1"]
    assert len(entries) >= 40
    urls = [e["url"] for e in entries]
    assert len(urls) == len(set(urls)), "URLs must be distinct (dedup collapses duplicates)"
    for e in entries:
        assert e["url"].startswith("http")
        assert e["name"]
        assert 1 <= int(e["authority"]) <= 5


def test_merge_expands_official_busca1_sources():
    base = _load("official_sources_manifest.json")
    countries = _load("official_sources_countries.json")
    sw = base.setdefault("workstreams", {})
    for ws, extra in countries["workstreams"].items():
        sw[ws] = list(sw.get(ws, [])) + extra
    rows = manifest_sources(base, "busca1")
    assert len(rows) >= 50
    # broad country coverage
    covered = {e.get("country") for e in countries["workstreams"]["busca1"] if e.get("country")}
    assert len(covered) >= 30
