from nutev.querypacks.longitudinal_adherence_terms import (
    longitudinal_adherence_document_terms,
    longitudinal_adherence_terms,
)


def test_longitudinal_adherence_terms_cover_maintenance_and_remission() -> None:
    terms = {term.lower() for term in longitudinal_adherence_terms()}

    assert "long-term dietary adherence" in terms
    assert "weight regain prevention" in terms
    assert "type 2 diabetes remission maintenance" in terms
    assert "relapse prevention" in terms


def test_longitudinal_adherence_document_terms_are_specific() -> None:
    terms = {term.lower() for term in longitudinal_adherence_document_terms()}

    assert "weight loss maintenance systematic review" in terms
    assert "diabetes remission maintenance trial" in terms
    assert "longitudinal adherence study" in terms


def test_longitudinal_adherence_terms_are_deduplicated_case_insensitively() -> None:
    terms = longitudinal_adherence_terms()
    lowered = [term.lower() for term in terms]

    assert len(lowered) == len(set(lowered))
