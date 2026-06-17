from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES


def test_obesity_cardiometabolic_category_covers_ckm_terms() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["obesity_cardiometabolic"]}

    assert "cardiovascular-kidney-metabolic syndrome" in terms
    assert "cardiovascular kidney metabolic syndrome" in terms
    assert "cardiovascular-kidney-metabolic risk" in terms
    assert "ckm syndrome" in terms
    assert "cardiorenal metabolic syndrome" in terms
