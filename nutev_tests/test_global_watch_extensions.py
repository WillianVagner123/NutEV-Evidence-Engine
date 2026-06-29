from __future__ import annotations

from nutev.global_watch import watch_config
from nutev.global_watch.watch_extensions import (
    PERSONALIZED_NUTRITION_CARDIOMETABOLIC_TERMS,
    PERSONALIZED_NUTRITION_IMPLEMENTATION_TERMS,
    apply_watch_taxonomy_extensions,
)


def test_watch_taxonomy_extensions_apply_to_flat_category_lists(monkeypatch) -> None:
    base_terms = ["personalized nutrition", "precision nutrition"]
    monkeypatch.setitem(
        watch_config.WATCH_CATEGORIES,
        "personalized_nutrition",
        list(base_terms),
    )

    apply_watch_taxonomy_extensions()

    extended_terms = watch_config.WATCH_CATEGORIES["personalized_nutrition"]
    assert extended_terms[: len(base_terms)] == base_terms
    assert "precision nutrition diabetes remission" in extended_terms
    assert "personalized nutrition adherence" in extended_terms


def test_watch_taxonomy_extensions_remain_idempotent_for_flat_lists(monkeypatch) -> None:
    monkeypatch.setitem(
        watch_config.WATCH_CATEGORIES,
        "personalized_nutrition",
        ["personalized nutrition"],
    )

    apply_watch_taxonomy_extensions()
    apply_watch_taxonomy_extensions()

    extended_terms = watch_config.WATCH_CATEGORIES["personalized_nutrition"]
    assert extended_terms.count("precision nutrition diabetes remission") == 1
    assert extended_terms.count("personalized nutrition adherence") == 1


def test_watch_taxonomy_extensions_still_apply_to_grouped_category_lists(monkeypatch) -> None:
    monkeypatch.setitem(
        watch_config.WATCH_CATEGORIES,
        "personalized_nutrition",
        [["personalized nutrition"], ["precision nutrition adherence"]],
    )

    apply_watch_taxonomy_extensions()

    grouped_terms = watch_config.WATCH_CATEGORIES["personalized_nutrition"]
    assert PERSONALIZED_NUTRITION_CARDIOMETABOLIC_TERMS[-1] in grouped_terms[0]
    assert PERSONALIZED_NUTRITION_IMPLEMENTATION_TERMS[-1] in grouped_terms[1]
