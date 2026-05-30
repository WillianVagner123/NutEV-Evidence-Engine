from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES


def test_implementation_behavior_includes_weight_maintenance_terms() -> None:
    terms = {term.lower() for term in WATCH_CATEGORIES["implementation_behavior"]}

    assert "weight loss maintenance" in terms
    assert "long-term weight maintenance" in terms
    assert "weight regain" in terms
    assert "weight regain prevention" in terms
    assert "relapse prevention" in terms
    assert "habit formation" in terms
