from __future__ import annotations

from nutev.global_watch.watch_scoring import score_watch_item


def test_high_value_document_type_is_demoted_without_nutmev_scope() -> None:
    unrelated = score_watch_item(
        {
            "title": "Clinical practice guideline for dermatology care",
            "source_provider": "pubmed",
        }
    )
    scoped = score_watch_item(
        {
            "title": "Clinical practice guideline for obesity nutrition care",
            "source_provider": "pubmed",
        }
    )

    assert scoped > unrelated
    assert scoped - unrelated >= 45


def test_scope_guard_does_not_penalize_dietary_evidence_synthesis() -> None:
    assert score_watch_item({"title": "Systematic review of dietary adherence"}) > score_watch_item(
        {"title": "Systematic review of dermatology care"}
    )


def test_ckm_nutrition_statement_is_scoped_and_prioritized() -> None:
    ckm_statement = score_watch_item(
        {
            "title": "Scientific statement on CKM nutrition and cardiometabolic risk",
            "source_provider": "pubmed",
        }
    )
    unrelated_statement = score_watch_item(
        {
            "title": "Scientific statement on dermatology care",
            "source_provider": "pubmed",
        }
    )

    assert ckm_statement > unrelated_statement
    assert ckm_statement - unrelated_statement >= 45
