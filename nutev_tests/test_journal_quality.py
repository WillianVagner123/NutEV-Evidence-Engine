from __future__ import annotations

from nutev.analysis.journal_quality import (
    derive_quality_score,
    enrich_journal_quality,
    fetch_journal_metrics,
    normalize_issn,
    save_metrics_cache,
    score_journal,
)


def test_derive_quality_score_signals():
    # quartile is the strongest signal; high h-index lifts Q1 to elite
    assert derive_quality_score(quartile="Q1", h_index=200) == 10
    assert derive_quality_score(quartile="Q1") == 8
    assert derive_quality_score(quartile="Q3") == 6
    # h-index path (no quartile)
    assert derive_quality_score(h_index=200) == 10  # Nature tier
    assert derive_quality_score(h_index=50) == 7
    assert derive_quality_score(h_index=5) == 4
    # DOAJ-only / seal floor
    assert derive_quality_score(is_in_doaj=True) == 5
    assert derive_quality_score(is_in_doaj=True, has_doaj_seal=True) == 8
    # predatory (and not legitimised by DOAJ) is auto-low
    assert derive_quality_score(is_predatory=True, h_index=300) == 1
    # source types
    assert derive_quality_score(source_type="repository", h_index=999) == 5
    assert derive_quality_score(source_type="conference") == 5
    # not enough signal
    assert derive_quality_score() is None


def test_normalize_issn():
    assert normalize_issn("15432165") == "1543-2165"
    assert normalize_issn("1543-2165") == "1543-2165"
    assert normalize_issn("2049-3258") == "2049-3258"


def test_fetch_and_score_offline_use_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")
    save_metrics_cache(tmp_path, {"1543-2165": {"h_index": 200, "is_in_doaj": False, "type": "journal"}})
    assert fetch_journal_metrics("1543-2165", config_root=tmp_path)["h_index"] == 200
    assert score_journal("1543-2165", config_root=tmp_path) == 10
    # unknown ISSN offline -> empty / None (no network)
    assert fetch_journal_metrics("0000-0000", config_root=tmp_path) == {}
    assert score_journal("0000-0000", config_root=tmp_path) is None


def test_enrich_journal_quality_offline(tmp_path, monkeypatch):
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")
    save_metrics_cache(tmp_path, {"1543-2165": {"h_index": 30, "is_in_doaj": True, "type": "journal"}})
    rows = [
        {"title": "a", "issn": "1543-2165"},
        {"title": "b"},  # no issn -> untouched
    ]
    enrich_journal_quality(rows, config_root=tmp_path)
    assert rows[0]["journal_quality_score"] == 6  # h_index 30 -> GOOD
    assert rows[0]["journal_in_doaj"] is True
    assert "journal_quality_score" not in rows[1]
