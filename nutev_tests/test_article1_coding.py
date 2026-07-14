"""Tests for the Article 1 analytical coding (tracks, A/B/C/D, AACODS)."""
from __future__ import annotations

from pathlib import Path

from nutev.analysis.article1_coding import (
    aacods_fields,
    article1_record_fields,
    classify_track,
    code_context_flags,
    code_domains,
    provenance_fields,
    sha256_of_file,
    who_region,
)


def test_classify_track_from_provider():
    assert classify_track({"source_provider": "pubmed"}) == "indexed_database"
    assert classify_track({"source_provider": "crossref"}) == "indexed_database"
    assert classify_track({"source_provider": "official_web"}) == "guideline_repository"
    assert classify_track({"source_institution": "FAO"}) == "guideline_repository"
    assert classify_track({"source_institution": "American Heart Association"}) == "society_website"
    # Unknown provenance is conservatively counted under "other methods".
    assert classify_track({"source_provider": "mystery"}) == "hand_search"


def test_classify_track_explicit_wins():
    rec = {"track": "linked_implementation_material", "source_provider": "pubmed"}
    assert classify_track(rec) == "linked_implementation_material"


def test_domain_substantive_rule_rejects_mere_mention():
    # Short rhetorical mention of cooking (domain B) with no actionable context.
    rec = {"title": "It is important to cook.", "abstract": "", "source_type": "research"}
    coded = code_domains(rec)
    assert coded["domain_B"] is False
    assert coded["n_domains"] == 0
    assert coded["profile"] == ""


def test_domain_marked_when_actionable_and_substantive():
    text = (
        "This guidance recommends improving diet quality by increasing fruit and "
        "vegetable intake, and provides a strategy to build cooking skills and meal "
        "planning to support adherence. " * 3
    )
    rec = {"title": "Healthy eating strategy", "abstract": text, "source_type": "guideline"}
    coded = code_domains(rec)
    assert coded["domain_A"] is True   # diet quality / fruit and vegetable
    assert coded["domain_B"] is True   # cooking skills / meal planning
    assert coded["domain_D"] is True   # adherence
    assert "A" in coded["profile"] and "D" in coded["profile"]
    assert coded["n_domains"] == coded["profile"].__len__()
    assert coded["domain_coding_needs_human_review"] is True


def test_guideline_document_is_substantive_even_if_short():
    rec = {"title": "National dietary pattern guideline", "abstract": "sodium", "source_type": "official_guide"}
    coded = code_domains(rec)
    # A guideline doc gives guidance by purpose -> keyword 'sodium'/'dietary pattern' counts.
    assert coded["domain_A"] is True


def test_context_flags_cost_and_equity():
    rec = {"abstract": "This program improves affordability and reduces socioeconomic disparities."}
    flags = code_context_flags(rec)
    assert flags["mentions_cost"] is True
    assert flags["mentions_equity"] is True


def test_aacods_authority_and_date_autofilled_rest_human():
    rec = {"source_institution": "Ministry of Health", "year": 2021}
    a = aacods_fields(rec)
    assert a["authority"] == "tier_1"       # government
    assert a["date_currency"] == "2021"
    assert a["accuracy"] == "" and a["coverage"] == "" and a["objectivity"] == "" and a["significance"] == ""
    assert a["aacods_needs_human_review"] is True


def test_who_region_and_income_band_not_guessed():
    assert who_region({"country": "Brazil"}) == "AMR"
    assert who_region({"country": "Portugal"}) == "EUR"
    assert who_region({"country": "Atlantis"}) == ""
    prov = provenance_fields({"country": "Brazil"})
    assert prov["who_region"] == "AMR"
    assert prov["income_band"] == ""  # never guessed


def test_sha256_of_file(tmp_path: Path):
    p = tmp_path / "doc.pdf"
    p.write_bytes(b"%PDF-1.4 test content")
    digest = sha256_of_file(p)
    assert digest and len(digest) == 64
    assert sha256_of_file(tmp_path / "missing.pdf") is None


def test_article1_record_fields_bundles_everything(tmp_path: Path):
    p = tmp_path / "guide.pdf"
    p.write_bytes(b"content")
    rec = {
        "source_provider": "official_web",
        "source_institution": "FAO",
        "country": "Brazil",
        "title": "Dietary guideline",
        "source_type": "official_guide",
        "abstract": "recommends improving diet quality",
        "archived_pdf_path": str(p),
    }
    fields = article1_record_fields(rec)
    assert fields["track"] == "guideline_repository"
    assert fields["who_region"] == "AMR"
    assert fields["domain_A"] is True
    assert fields["archived_pdf_sha256"] and len(fields["archived_pdf_sha256"]) == 64
    assert fields["authority"] == "tier_1"
