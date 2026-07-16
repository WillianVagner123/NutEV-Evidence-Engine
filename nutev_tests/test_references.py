"""Tests for the citable-reference builder."""
from __future__ import annotations

from nutev.analysis.references import build_reference, format_reference, reference_fields


def test_full_reference_includes_all_present_parts():
    rec = {
        "issuing_body": "Ministry of Health",
        "title": "Dietary Guidelines for Brazilians",
        "country": "Brazil",
        "document_version": "2014",
        "official_url": "https://saude.gov.br/guia.pdf",
        "access_date": "2026-07-16T00:00:00+00:00",
        "archived_pdf_sha256": "abc123",
    }
    ref = format_reference(rec)
    assert "Ministry of Health" in ref
    assert "Dietary Guidelines for Brazilians" in ref
    assert "Brazil" in ref and "2014" in ref
    assert "Disponível em: https://saude.gov.br/guia.pdf" in ref
    assert "Acesso em: 2026-07-16" in ref
    assert "SHA-256: abc123" in ref


def test_reference_omits_missing_fields():
    ref = format_reference({"title": "Just a Title"})
    assert ref == "Just a Title."
    assert "Disponível em" not in ref and "SHA-256" not in ref


def test_reference_falls_back_across_keys():
    # institution -> reference_institution; url falls back to source_url.
    f = reference_fields({"institution": "WHO", "source_url": "https://who.int/x"})
    assert f["reference_institution"] == "WHO"
    assert f["reference_url"] == "https://who.int/x"


def test_build_reference_returns_string_and_fields():
    out = build_reference({"name": "FAO FBDG", "sha256": "deadbeef"})
    assert out["reference"].startswith("FAO FBDG")
    assert out["reference_sha256"] == "deadbeef"


def test_empty_record_is_safe():
    assert format_reference({}) == ""
    assert build_reference({})["reference"] == ""
