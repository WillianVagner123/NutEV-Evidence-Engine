from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES


def test_obesity_cardiometabolic_category_preserves_ckm_search_terms() -> None:
    rendered = "\n".join(WATCH_CATEGORIES["obesity_cardiometabolic"]).lower()

    assert "cardiovascular-kidney-metabolic syndrome" in rendered
    assert "cardiovascular kidney metabolic nutrition" in rendered
    assert "cardio-kidney-metabolic syndrome" in rendered
    assert "cardio kidney metabolic nutrition" in rendered
    assert "ckm syndrome" in rendered
    assert "ckm nutrition" in rendered
