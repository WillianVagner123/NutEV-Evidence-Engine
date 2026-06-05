from __future__ import annotations

from nutev.global_watch.watch_scoring import score_watch_item


def test_high_value_document_type_needs_nutmev_scope_for_top_priority() -> None:
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
    assert unrelated < 80


def test_scope_guard_does_not_penalize_dietary_evidence_synthesis() -> None:
    assert score_watch_item({"title": "Systematic review of dietary adherence"}) > score_watch_item(
        {"title": "Systematic review of dermatology care"}
    )
