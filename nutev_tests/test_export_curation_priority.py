from nutev.export.curation import _is_prioritized


def test_priority_term_requires_token_boundary() -> None:
    row = {
        "title": "Mindfulness training for sleep quality",
        "relevance_score": 8,
    }

    assert not _is_prioritized(row)


def test_priority_term_matches_normalized_phrase() -> None:
    row = {
        "title": "Plant based diet adherence in cardiometabolic risk",
        "relevance_score": 8,
    }

    assert _is_prioritized(row)
