from nutev.global_watch.behavior_terms import controlled_behavior_terms


def test_controlled_behavior_terms_cover_nutmev_implementation_gaps() -> None:
    terms = controlled_behavior_terms()

    assert "long-term adherence" in terms
    assert "weight regain prevention" in terms
    assert "pragmatic nutrition intervention" in terms
    assert "hybrid effectiveness-implementation trial" in terms
    assert "barriers and facilitators" in terms
    assert "implementation intentions" in terms


def test_controlled_behavior_terms_are_stable_and_deduplicated() -> None:
    terms = controlled_behavior_terms()

    assert terms == controlled_behavior_terms()
    assert len(terms) == len({term.lower() for term in terms})
