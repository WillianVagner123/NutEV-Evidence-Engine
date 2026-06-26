from __future__ import annotations

from nutev.global_watch.watch_config import WATCH_CATEGORIES


OBESITY_PHARMACOTHERAPY_TERMS = {
    "anti-obesity medication nutrition",
    "anti-obesity medication dietary counseling",
    "obesity pharmacotherapy nutrition care",
    "obesity pharmacotherapy dietary counseling",
    "glp-1 nutrition",
    "glp-1 dietary counseling",
    "glp-1 receptor agonist nutrition",
    "glp-1 receptor agonist dietary counseling",
    "incretin therapy nutrition care",
    "incretin therapy dietary counseling",
}

IMPLEMENTATION_PHARMACOTHERAPY_TERMS = {
    "anti-obesity medication lifestyle intervention",
    "anti-obesity medication nutrition intervention",
    "anti-obesity medication adherence",
    "anti-obesity medication weight maintenance",
    "obesity pharmacotherapy lifestyle intervention",
    "obesity pharmacotherapy nutrition intervention",
    "obesity pharmacotherapy dietary adherence",
    "glp-1 lifestyle intervention",
    "glp-1 nutrition intervention",
    "glp-1 dietary adherence",
    "glp-1 weight maintenance",
    "glp-1 receptor agonist lifestyle intervention",
    "glp-1 receptor agonist nutrition intervention",
    "incretin therapy lifestyle intervention",
    "incretin therapy nutrition intervention",
}

NUTMEV_ANCHORS = (
    "nutrition",
    "dietary",
    "lifestyle",
    "adherence",
    "maintenance",
)


def test_obesity_pharmacotherapy_watch_terms_remain_nutrition_anchored() -> None:
    terms = set(WATCH_CATEGORIES["obesity_cardiometabolic"])

    assert OBESITY_PHARMACOTHERAPY_TERMS <= terms
    assert all(any(anchor in term for anchor in NUTMEV_ANCHORS) for term in OBESITY_PHARMACOTHERAPY_TERMS)


def test_implementation_pharmacotherapy_watch_terms_remain_behavior_anchored() -> None:
    terms = set(WATCH_CATEGORIES["implementation_behavior"])

    assert IMPLEMENTATION_PHARMACOTHERAPY_TERMS <= terms
    assert all(any(anchor in term for anchor in NUTMEV_ANCHORS) for term in IMPLEMENTATION_PHARMACOTHERAPY_TERMS)


def test_pharmacotherapy_watch_terms_do_not_add_bare_drug_queries() -> None:
    pharmacotherapy_terms = {
        term
        for terms in WATCH_CATEGORIES.values()
        for term in terms
        if "glp-1" in term or "incretin" in term or "anti-obesity medication" in term
    }

    assert "glp-1" not in pharmacotherapy_terms
    assert "incretin therapy" not in pharmacotherapy_terms
    assert "anti-obesity medication" not in pharmacotherapy_terms
