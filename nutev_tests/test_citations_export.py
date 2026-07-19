"""BibTeX / RIS reference-manager export (S9) — never invents, degrades cleanly."""
from __future__ import annotations

from pathlib import Path

from nutev.export.citations import (
    citation_key,
    to_bibtex,
    to_ris,
    write_bibtex,
    write_ris,
)

_ROWS = [
    {
        "document_id": "d1",
        "title": "Mediterranean diet and cardiometabolic outcomes",
        "authors": "Silva J; Doe A",
        "journal": "Nutrition Reviews",
        "year": "2021",
        "doi": "10.1000/abc",
        "final_url": "https://doi.org/10.1000/abc",
        "article_type": "systematic_review",
    },
    {
        "document_id": "d2",
        "title": "Guia alimentar para a população brasileira",
        "authors": ["Ministério da Saúde"],
        "source_institution": "Ministério da Saúde",
        "year": "2014",
        "final_url": "https://saude.gov.br/guia",
        "article_type": "official_guideline",
        "country": "BR",
    },
]


def test_bibtex_has_entries_with_real_fields_only():
    bib = to_bibtex(_ROWS)
    assert "@article{" in bib          # journal review
    assert "@techreport{" in bib       # official guideline
    assert "title = {Mediterranean diet and cardiometabolic outcomes}" in bib
    assert "author = {Silva J and Doe A}" in bib
    assert "doi = {10.1000/abc}" in bib
    # No empty fields fabricated: d2 has no DOI, so no doi line for its entry.
    guideline_block = [b for b in bib.split("@") if "brasileira" in b][0]
    assert "doi =" not in guideline_block


def test_ris_types_and_authors():
    ris = to_ris(_ROWS)
    assert "TY  - JOUR" in ris           # journal review
    assert "TY  - RPRT" in ris           # official guideline
    assert "AU  - Silva J" in ris and "AU  - Doe A" in ris
    assert "DO  - 10.1000/abc" in ris
    assert ris.count("ER  - ") == 2


def test_rows_without_identity_are_skipped_not_fabricated():
    rows = [{"document_id": "x", "authors": "Nobody"}]  # no title/doi/url
    assert to_bibtex(rows).strip() == ""
    assert to_ris(rows).strip() == ""


def test_citation_keys_are_unique_and_stable():
    used: set[str] = set()
    k1 = citation_key(_ROWS[0], used)
    k2 = citation_key(_ROWS[0], used)  # same row again -> must not collide
    assert k1 != k2
    assert k1.startswith("silvaj2021")


def test_writers_emit_files_and_count(tmp_path: Path):
    n_bib = write_bibtex(_ROWS, tmp_path / "refs.bib")
    n_ris = write_ris(_ROWS, tmp_path / "refs.ris")
    assert n_bib == 2 and n_ris == 2
    assert (tmp_path / "refs.bib").read_text(encoding="utf-8").startswith("@")
    assert "TY  -" in (tmp_path / "refs.ris").read_text(encoding="utf-8")
