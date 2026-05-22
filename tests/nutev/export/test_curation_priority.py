from __future__ import annotations

from nutev.export.curation import _curate_row


def test_curated_priority_uses_abstract_nutev_signals() -> None:
    curated = _curate_row(
        {
            "title": "Community nutrition implementation outcomes",
            "abstract": (
                "Food and nutrition literacy with teaching kitchens for adults "
                "with obesity and cardiometabolic risk."
            ),
            "workstream": "busca2b",
            "relevance_score": 9,
            "evidence_type": "systematic_review",
        }
    )

    assert curated["is_prioritized"] is True


def test_curated_priority_stays_false_without_scope_signals() -> None:
    curated = _curate_row(
        {
            "title": "Community service process metrics",
            "abstract": "Administrative staffing update for a local service.",
            "workstream": "busca2b",
            "relevance_score": 9,
            "evidence_type": "study",
        }
    )

    assert curated["is_prioritized"] is False


def test_curated_priority_keeps_editorial_high_value_documents() -> None:
    curated = _curate_row(
        {
            "title": "Adult clinical nutrition pathway",
            "workstream": "busca2a",
            "relevance_score": 7,
            "editorial_priority_tier": "a1_proxy_high",
            "evidence_type": "guideline",
        }
    )

    assert curated["is_prioritized"] is True
