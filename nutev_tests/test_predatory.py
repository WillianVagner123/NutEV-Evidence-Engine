from __future__ import annotations

import json

from nutev.analysis.journal_quality import enrich_journal_quality
from nutev.analysis.predatory import is_predatory, load_predatory_index


def _write_overlay(config_root, **lists):
    (config_root / "predatory_journals.json").write_text(
        json.dumps({"publishers": [], "journals": [], "issns": [], **lists}),
        encoding="utf-8",
    )


def test_overlay_matching_offline(tmp_path, monkeypatch):
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")  # no SPJ fetch
    _write_overlay(
        tmp_path,
        journals=["Bogus Journal of Everything"],
        publishers=["Shady Open Press"],
        issns=["1234-5678"],
    )
    index = load_predatory_index(tmp_path)
    assert is_predatory(journal="bogus journal of everything", index=index)  # case-insensitive
    assert is_predatory(publisher="Shady Open Press", index=index)
    assert is_predatory(issn="12345678", index=index)  # normalized to 1234-5678
    assert not is_predatory(journal="The Lancet", index=index)


def test_load_index_offline_no_overlay(tmp_path, monkeypatch):
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")
    index = load_predatory_index(tmp_path)
    assert index == {"names": set(), "issns": set()}
    assert not is_predatory(journal="anything", index=index)


def test_enrich_predatory_forces_low_score(tmp_path, monkeypatch):
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")
    _write_overlay(tmp_path, journals=["Bogus Journal of Everything"])
    rows = [{"title": "x", "journal": "Bogus Journal of Everything"}]  # no ISSN, no metrics
    enrich_journal_quality(rows, config_root=tmp_path)
    assert rows[0]["journal_quality_score"] == 1


def test_doaj_rescues_predatory(tmp_path, monkeypatch):
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")
    _write_overlay(tmp_path, journals=["Edge Case Journal"])
    # ISSN present + seeded metrics cache says it is DOAJ-indexed -> not auto-1
    (tmp_path / "journal_quality_cache.json").write_text(
        json.dumps({"2049-3258": {"h_index": None, "is_in_doaj": True, "type": "journal"}}),
        encoding="utf-8",
    )
    rows = [{"title": "y", "journal": "Edge Case Journal", "issn": "2049-3258"}]
    enrich_journal_quality(rows, config_root=tmp_path)
    assert rows[0]["journal_quality_score"] == 5  # DOAJ floor, not predatory 1
