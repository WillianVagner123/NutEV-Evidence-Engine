"""Tests for the corpus report (fuzzy dedup + clustering + heatmap Excel)."""
from __future__ import annotations

from pathlib import Path

import pytest

import nutev.analysis.corpus_report as cr

_ROWS = [
    {"name": "Brazil FBDG", "country": "brazil", "extracted_text":
     "This guideline recommends fruit and vegetables and whole grains for diet quality. " * 6,
     "domain_A": True, "domain_B": False, "domain_C": True, "domain_D": True, "profile": "ACD",
     "n_domains": 3, "n_key_phrases": 4, "top_terms": "fruit|vegetables|whole|grains"},
    {"name": "Brazil FBDG (mirror)", "country": "brazil", "extracted_text":
     "This guideline recommends fruit and vegetables and whole grains for diet quality. " * 6,
     "domain_A": True, "domain_B": False, "domain_C": True, "domain_D": True, "profile": "ACD",
     "n_domains": 3, "n_key_phrases": 4, "top_terms": "fruit|vegetables|whole|grains"},
    {"name": "Kenya guideline", "country": "kenya", "extracted_text":
     "Families should share meals together to strengthen commensality and adherence. " * 6,
     "domain_A": False, "domain_B": False, "domain_C": True, "domain_D": True, "profile": "CD",
     "n_domains": 2, "n_key_phrases": 2, "top_terms": "families|meals|commensality"},
]


def test_report_skips_gracefully_without_deps(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(cr, "report_dependencies_available", lambda: False)
    result = cr.write_corpus_report([dict(r) for r in _ROWS], tmp_path)
    assert result["status"] == "skipped"
    assert "install" in result and "report" in result["install"]
    # Nothing written when skipped.
    assert not (tmp_path / "NUTEV_GUIDES_REPORT.xlsx").exists()


def test_doc_signature_falls_back_to_coded_fields():
    # No extracted_text -> use name + key phrases + top terms (checkpoint case).
    sig = cr._doc_signature({"name": "X", "key_phrases_text": "[A] eat well", "top_terms": "a|b|c"})
    assert "eat well" in sig and "a b c" in sig


def test_fuzzy_dedup_groups_near_duplicates():
    pytest.importorskip("sklearn")
    rows, pairs = cr.fuzzy_dedup([dict(r) for r in _ROWS], threshold=0.8)
    # The two Brazil mirrors should land in the same dedup group.
    brazil = [r for r in rows if r["country"] == "brazil"]
    assert brazil[0]["dedup_group"] == brazil[1]["dedup_group"]
    # Exactly one of them is marked a duplicate of the other.
    dups = [r for r in brazil if r.get("dedup_is_duplicate_of")]
    assert len(dups) == 1
    assert any(p["similarity"] >= 0.8 for p in pairs)


def test_write_corpus_report_end_to_end(tmp_path: Path):
    pytest.importorskip("sklearn")
    pytest.importorskip("matplotlib")
    result = cr.write_corpus_report([dict(r) for r in _ROWS], tmp_path, threshold=0.8)
    assert result["status"] == "ok"
    assert result["duplicates_marked"] >= 1
    assert (tmp_path / "NUTEV_GUIDES_REPORT.xlsx").exists()
