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


def test_prediabetes_prevention_program_terms_receive_operational_priority() -> None:
    generic = score_watch_item({"title": "Lifestyle program implementation in primary care"})
    targeted = score_watch_item(
        {
            "title": "Prediabetes prevention program with dietitian-led nutrition counseling",
            "source_provider": "pubmed",
        }
    )

    assert targeted > generic
    assert targeted - generic >= 20
