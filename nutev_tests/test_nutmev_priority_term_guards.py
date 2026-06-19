from __future__ import annotations

from nutev.export.curation import _PRIORITY_TERMS
from nutev.global_watch.watch_config import WATCH_CATEGORIES


def test_global_watch_keeps_diabetes_remission_terms_in_cardiometabolic_scope() -> None:
    cardiometabolic_terms = {
        term.lower() for term in WATCH_CATEGORIES["obesity_cardiometabolic"]
    }

    assert "type 2 diabetes remission" in cardiometabolic_terms
    assert "diabetes remission" in cardiometabolic_terms
    assert "remission of type 2 diabetes" in cardiometabolic_terms


def test_curated_priority_terms_keep_core_nutmev_domains() -> None:
    priority_terms = {_normalize(term) for term in _PRIORITY_TERMS}

    assert "masld" in priority_terms
    assert "nafld" in priority_terms
    assert "food and nutrition literacy" in priority_terms
    assert "food is medicine" in priority_terms
    assert "implementation science" in priority_terms
    assert "clinical practice guideline" in priority_terms


def _normalize(term: str) -> str:
    return str(term).strip().lower()
