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


def test_ckm_guidance_is_treated_as_nutmev_cardiometabolic_scope() -> None:
    ckm_guidance = score_watch_item(
        {
            "title": "Scientific statement on cardiovascular-kidney-metabolic health",
            "source_provider": "pubmed",
        }
    )
    unrelated_guidance = score_watch_item(
        {
            "title": "Scientific statement on dermatology care delivery",
            "source_provider": "pubmed",
        }
    )

    assert ckm_guidance > unrelated_guidance
    assert ckm_guidance - unrelated_guidance >= 45
