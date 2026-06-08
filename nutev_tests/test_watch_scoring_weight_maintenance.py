from __future__ import annotations

import importlib


def _score_watch_item(item: dict) -> float:
    module = importlib.import_module("nutev.global_watch.watch_scoring")
    return float(module.score_watch_item(item))


def test_weight_regain_prevention_scores_above_generic_obesity_note() -> None:
    boosted = _score_watch_item(
        {
            "title": "Weight regain prevention and relapse prevention after obesity lifestyle intervention",
            "source_provider": "pubmed",
        }
    )
    baseline = _score_watch_item(
        {
            "title": "Obesity lifestyle intervention note",
            "source_provider": "pubmed",
        }
    )

    assert boosted > baseline


def test_weight_maintenance_without_diet_word_keeps_nutmev_scope() -> None:
    scored = _score_watch_item(
        {
            "title": "Weight maintenance and behavioral maintenance after cardiometabolic lifestyle intervention",
            "source_provider": "pubmed",
        }
    )
    generic = _score_watch_item(
        {
            "title": "Cardiometabolic lifestyle intervention note",
            "source_provider": "pubmed",
        }
    )

    assert scored > generic
