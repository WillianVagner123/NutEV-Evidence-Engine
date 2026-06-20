from __future__ import annotations

from nutev.export.curation import _is_prioritized


def test_curated_priority_terms_cover_metabolic_steatotic_liver_terms() -> None:
    row = {
        "title": "Nutrition care for MASH and steatotic liver disease",
        "abstract": "Adult cardiometabolic nutrition guidance for metabolic dysfunction-associated steatohepatitis.",
        "relevance_score": 8,
    }

    assert _is_prioritized(row) is True


def test_curated_liver_priority_terms_still_require_minimum_score() -> None:
    row = {
        "title": "Nutrition care for MASH and steatotic liver disease",
        "abstract": "Adult cardiometabolic nutrition guidance for metabolic dysfunction-associated steatohepatitis.",
        "relevance_score": 6,
    }

    assert _is_prioritized(row) is False
