from __future__ import annotations

from nutev.export.curation import _curate_row


def test_curated_priority_detects_food_is_medicine_variants() -> None:
    curated = _curate_row(
        {
            "document_id": "doc-1",
            "title": "Food-as-Medicine produce prescription for cardiometabolic risk",
            "relevance_score": 9,
            "workstream": "busca2b",
            "download_status": "metadata_only",
        }
    )

    assert curated["is_prioritized"] is True


def test_curated_priority_keeps_minimum_score_threshold() -> None:
    curated = _curate_row(
        {
            "document_id": "doc-2",
            "title": "Medically tailored meals and food environment intervention",
            "relevance_score": 7,
            "workstream": "busca2b",
            "download_status": "metadata_only",
        }
    )

    assert curated["is_prioritized"] is False
