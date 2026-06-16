from __future__ import annotations

from nutev.analysis.enrich_geo import country_from_text, enrich_record


def test_country_from_text_single_country():
    assert country_from_text("Universidade de São Paulo, São Paulo, Brazil") == ["BR"]


def test_country_from_text_usa_variant():
    assert country_from_text("Harvard Medical School, Boston, MA, USA") == ["US"]


def test_country_from_text_multi_affiliation_order_preserved():
    joined = (
        "Universidade Federal, Rio de Janeiro, Brazil; "
        "University of Oxford, Oxford, United Kingdom"
    )
    assert country_from_text(joined) == ["BR", "GB"]


def test_country_from_text_empty_and_none():
    assert country_from_text("") == []
    assert country_from_text(None) == []


def test_country_from_text_dedupes_repeated_country():
    text = "Dept A, Brazil; Dept B, Brasil; Dept C, Brazil"
    assert country_from_text(text) == ["BR"]


def test_country_from_text_longest_name_wins_niger_vs_nigeria():
    # "Nigeria" must not be misread as "Niger" (NE).
    assert country_from_text("University of Lagos, Lagos, Nigeria") == ["NG"]
    assert country_from_text("University of Niamey, Niger") == ["NE"]


def test_country_from_text_united_states_over_substring():
    assert country_from_text("United States of America") == ["US"]
    assert country_from_text("United States") == ["US"]


def test_country_from_text_uk_subnations_map_to_gb():
    assert country_from_text("School of Medicine, Edinburgh, Scotland") == ["GB"]
    assert country_from_text("Cardiff University, Wales, UK") == ["GB"]


def test_country_from_text_no_false_positive_inside_word():
    # "Oman" inside "Romania" / "oman" inside "woman" must not match Oman.
    assert "OM" not in country_from_text("Bucharest, Romania")
    assert country_from_text("Bucharest, Romania") == ["RO"]


def test_enrich_record_country_from_affiliations_list():
    out = enrich_record({"affiliations": ["Universidade Federal, Brazil"]})
    assert out["countries"] == ["BR"]
    assert out["country"] == "BR"
    assert out["region"] == "South America"


def test_enrich_record_country_from_affiliation_string():
    out = enrich_record({"affiliation": "Harvard Medical School, Boston, MA, USA"})
    assert out["countries"] == ["US"]
    assert out["region"] == "North America"


def test_enrich_record_openalex_country_codes_take_precedence():
    # When structured country_codes exist, affiliations are NOT consulted.
    out = enrich_record(
        {"country_codes": ["DE"], "affiliations": ["Somewhere, Brazil"]}
    )
    assert out["countries"] == ["DE"]
    assert out["region"] == "Europe"
