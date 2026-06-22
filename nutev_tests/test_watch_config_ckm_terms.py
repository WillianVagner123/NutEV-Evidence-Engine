from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES


def _rendered_category(category: str) -> str:
    return "\n".join(WATCH_CATEGORIES[category]).lower()


def test_obesity_cardiometabolic_config_covers_ckm_terminology() -> None:
    rendered = _rendered_category("obesity_cardiometabolic")

    assert "cardiovascular-kidney-metabolic syndrome" in rendered
    assert "cardiovascular kidney metabolic syndrome" in rendered
    assert "cardio-kidney-metabolic syndrome" in rendered
    assert "cardio kidney metabolic syndrome" in rendered
    assert "ckm syndrome" in rendered
    assert "ckm nutrition" in rendered


def test_ckm_terms_remain_anchored_to_nutrition_scope() -> None:
    rendered = _rendered_category("obesity_cardiometabolic")

    assert "cardiovascular-kidney-metabolic nutrition" in rendered
    assert "cardiovascular kidney metabolic nutrition" in rendered
    assert "cardio-kidney-metabolic nutrition" in rendered
    assert "cardio kidney metabolic nutrition" in rendered
