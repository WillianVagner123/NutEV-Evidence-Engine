from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES


def _flatten_terms(values: list[object]) -> set[str]:
    terms: set[str] = set()
    for value in values:
        if isinstance(value, list):
            terms.update(str(item).lower() for item in value)
            continue
        terms.add(str(value).lower())
    return terms


def test_personalized_nutrition_category_covers_digital_and_counseling_variants() -> None:
    terms = _flatten_terms(WATCH_CATEGORIES["personalized_nutrition"])

    assert "digital personalized nutrition" in terms
    assert "digital personalised nutrition" in terms
    assert "personalized nutrition coaching" in terms
    assert "personalised nutrition coaching" in terms
    assert "tailored dietary counseling" in terms
    assert "tailored dietary counselling" in terms
