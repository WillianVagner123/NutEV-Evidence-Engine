from __future__ import annotations

from nutev.querypacks.semantic_coverage import missing_required_semantic_terms


def test_required_nutev_semantic_terms_are_covered() -> None:
    assert missing_required_semantic_terms() == {}


def test_semantic_coverage_reports_missing_terms() -> None:
    missing = missing_required_semantic_terms(
        {"busca2b": ["dietary adherence", "not a real nutev semantic term"]}
    )

    assert missing == {"busca2b": ["not a real nutev semantic term"]}
