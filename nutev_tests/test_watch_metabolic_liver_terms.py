from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES


def test_obesity_cardiometabolic_watch_terms_include_metabolic_liver_phenotypes() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["obesity_cardiometabolic"]}

    assert "hepatic fat" in terms
    assert "liver fat" in terms
    assert "intrahepatic fat" in terms
    assert "liver fibrosis" in terms
    assert "hepatic fibrosis" in terms
