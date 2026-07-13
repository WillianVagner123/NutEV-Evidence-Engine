"""Tests for the corpus-quality features:
#2 scope gate, #7 version/parallel-publication families, #8 open-access
fallback, and B country-discovery manifest gating.
"""
from __future__ import annotations

from pathlib import Path

from nutev.analysis.nutev_classifier import classify_evidence
from nutev.download.downloader import _open_access_candidates, _snapshot_candidates
from nutev.export.curation_patch import _classify_document_relations
from nutev.search.official_sources import load_official_manifest, manifest_sources

CONFIG = Path(__file__).resolve().parents[1] / "config"


# ---- #2 scope gate ---------------------------------------------------------

def test_scope_gate_flags_off_scope_and_keeps_dietary():
    diet = {"title": "Dietary guideline: increase vegetable and whole grain intake", "abstract": ""}
    pharma = {"title": "Semaglutide and anticoagulant drug therapy for venous thromboembolism", "abstract": ""}
    classify_evidence([diet, pharma], {"domains": {}, "outcomes": {}}, {"lenses": {}})
    assert diet["scope_status"] == "in_scope"
    assert diet["dietary_centrality"] == 1
    assert pharma["scope_status"] == "off_scope_review"
    assert "pharmacology" in pharma["scope_flags"] or "oncology_vte" in pharma["scope_flags"]
    assert pharma["dietary_centrality"] == 0


# ---- #7 version / parallel publication families ----------------------------

def test_document_relations_detect_annual_and_parallel():
    rows = [
        {"title": "Standards of Care in Diabetes", "year": "2025", "doi": "10.2337/dc25", "source_institution": "ADA"},
        {"title": "Standards of Care in Diabetes", "year": "2024", "doi": "10.2337/dc24", "source_institution": "ADA"},
        {"title": "Standards of Care in Diabetes", "year": "2023", "doi": "10.2337/dc23", "source_institution": "ADA"},
        {"title": "GLP-1 advisory statement", "year": "2026", "doi": "10.1/a", "source_institution": "AHA"},
        {"title": "GLP-1 advisory statement", "year": "2026", "doi": "10.2/b", "source_institution": "AHA"},
        {"title": "Unrelated dietary review", "year": "2020", "doi": "10.9/z", "source_institution": "X"},
    ]
    _classify_document_relations(rows)
    rels = {(r["title"], r["year"]): r["document_relation"] for r in rows}
    # Annual editions share a family; newest is primary, older are annual versions.
    assert rels[("Standards of Care in Diabetes", "2025")] == "primary_version"
    assert rels[("Standards of Care in Diabetes", "2024")] == "annual_version"
    assert rels[("Standards of Care in Diabetes", "2023")] == "annual_version"
    # Same-year different-DOI in one family -> parallel publication.
    glp1 = [r["document_relation"] for r in rows if r["title"] == "GLP-1 advisory statement"]
    assert "parallel_publication" in glp1
    # A lone document is standalone.
    assert rels[("Unrelated dietary review", "2020")] == "standalone"


# ---- #8 open-access fallback ----------------------------------------------

def test_open_access_candidates_from_pmcid_and_oa_url():
    rec = {"pmcid": "PMC12345", "oa_url": "https://example.org/oa.pdf"}
    cands = _open_access_candidates(rec)
    assert "https://pmc.ncbi.nlm.nih.gov/articles/PMC12345/" in cands
    assert "https://example.org/oa.pdf" in cands
    # bare numeric pmcid is normalized
    assert _open_access_candidates({"pmcid": "999"})[0].endswith("/PMC999/")


def test_snapshot_candidates_try_open_access_first():
    rec = {"pmcid": "PMC777", "doi": "10.1/x"}
    cands = _snapshot_candidates(rec, "https://blocked.publisher.com/pdf", "https://blocked.publisher.com/pdf")
    assert cands[0] == "https://pmc.ncbi.nlm.nih.gov/articles/PMC777/"


# ---- B country-discovery manifest gating ----------------------------------

def test_load_official_manifest_country_gating():
    with_countries = manifest_sources(load_official_manifest(CONFIG, include_countries=True), "busca1")
    without = manifest_sources(load_official_manifest(CONFIG, include_countries=False), "busca1")
    assert len(with_countries) > len(without)
    assert len(with_countries) >= 50
