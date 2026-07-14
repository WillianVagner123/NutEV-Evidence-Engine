"""Tests for the Article 1 reports (Domain Integration Matrix, two-track PRISMA)."""
from __future__ import annotations

from pathlib import Path

from nutev.export.article1_reports import (
    build_integration_matrix,
    build_two_track_prisma,
    write_integration_matrix,
)

# A small corpus with known domain coding, spread across tracks.
_GUIDE = {
    "source_provider": "official_web",
    "source_type": "official_guide",
    "title": "National dietary guideline",
    "abstract": "recommends diet quality, cooking skills, family meals and adherence strategy. affordability matters.",
}
_CLINICAL = {
    "source_provider": "pubmed",
    "source_type": "clinical_guideline",
    "title": "Clinical guideline",
    "abstract": "guidance on diet quality and adherence to treatment.",
}
_THIN = {
    "source_provider": "pubmed",
    "source_type": "research",
    "title": "A note",
    "abstract": "cooking is nice.",  # mere mention, not substantive -> no domains
}


def test_integration_matrix_blocks():
    m = build_integration_matrix([_GUIDE, _CLINICAL, _THIN])
    assert m["total"] == 3
    # Coverage: A appears in guide + clinical.
    assert m["domain_coverage"]["A"]["n"] == 2
    # The guide covers all four -> at least one all-four document.
    assert m["documents_with_all_four_domains"] >= 1
    # Profile distribution includes the thin doc as "none".
    assert "none" in m["profile_distribution"]
    # By-layer separates guias vs diretrizes.
    assert "guias" in m["by_layer"] and "diretrizes" in m["by_layer"]
    # Markers: cost mentioned by the guide.
    assert m["markers"]["mentions_cost"]["n"] >= 1
    assert m["markers"]["mentions_cost_and_offers_strategy"]["n"] >= 1


def test_write_integration_matrix_file_and_summary(tmp_path: Path):
    summary = write_integration_matrix([_GUIDE, _CLINICAL, _THIN], tmp_path)
    out = tmp_path / "NUTEV_DOMAIN_INTEGRATION_MATRIX.csv"
    assert out.exists()
    content = out.read_text(encoding="utf-8-sig")
    assert "domain_coverage" in content and "profile_distribution" in content and "by_layer" in content
    # Summary fields destined for run_summary.json.
    assert set(summary["domain_coverage"]) == {"A", "B", "C", "D"}
    assert "documents_with_all_four_domains" in summary
    assert isinstance(summary["profile_distribution"], dict)


def test_two_track_prisma_splits_databases_from_other_methods():
    prisma = build_two_track_prisma([_GUIDE, _CLINICAL, _THIN])
    # _CLINICAL and _THIN are pubmed (indexed); _GUIDE is guideline_repository.
    assert prisma["identified_from_databases"] == 2
    assert prisma["identified_from_other_methods"] == 1
    assert prisma["by_track"]["guideline_repository"] == 1
    assert prisma["by_track"]["indexed_database"] == 2
