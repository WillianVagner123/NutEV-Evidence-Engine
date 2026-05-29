from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES


def test_obesity_cardiometabolic_watch_terms_cover_glycemia_variants() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["obesity_cardiometabolic"]}

    assert "pre-diabetes" in terms
    assert "prediabetic state" in terms
    assert "impaired fasting glucose" in terms
    assert "impaired glucose tolerance" in terms
    assert "glucose intolerance" in terms
    assert "dysglycemia" in terms
    assert "dysglycaemia" in terms
    assert "diabetes prevention" in terms
    assert "diabetes prevention program" in terms
