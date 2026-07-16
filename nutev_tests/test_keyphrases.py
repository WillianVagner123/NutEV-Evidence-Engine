"""Tests for key-phrase / key-sentence extraction."""
from __future__ import annotations

from nutev.analysis.keyphrases import (
    extract_keyphrases,
    extract_keyphrases_from_pages,
    keyphrase_fields,
    split_sentences,
    top_terms,
)

_TEXT = (
    "This national dietary guideline recommends increasing fruit and vegetable intake. "
    "Families should share meals together to strengthen commensality. "
    "The weather today is sunny and pleasant. "
    "Health services must improve adherence and reduce barriers to implementation."
)


def test_split_sentences():
    s = split_sentences(_TEXT)
    assert len(s) == 4
    assert s[0].startswith("This national dietary guideline")


def test_extract_keyphrases_by_domain():
    phrases = extract_keyphrases(_TEXT)
    domains = {p["domain"] for p in phrases}
    # A (fruit/veg), C (commensality/shared meal), D (adherence/barrier).
    assert {"A", "C", "D"} <= domains
    # The A sentence with 'recommends' must be flagged actionable.
    a = [p for p in phrases if p["domain"] == "A"][0]
    assert a["actionable"] is True
    assert "fruit and vegetable" in a["sentence"].lower()
    # The off-topic weather sentence never appears.
    assert all("weather" not in p["sentence"].lower() for p in phrases)


def test_actionable_sentences_rank_first():
    text = (
        "Diet quality varies across regions. "
        "Guidelines recommend improving diet quality through whole grains."
    )
    phrases = [p for p in extract_keyphrases(text) if p["domain"] == "A"]
    assert phrases[0]["actionable"] is True  # the 'recommend' sentence ranks first


def test_top_terms_filters_stopwords():
    terms = top_terms(_TEXT)
    assert "dietary" in terms or "guideline" in terms
    assert "the" not in terms and "should" not in terms


def test_keyphrase_fields_shape():
    fields = keyphrase_fields({"extracted_text": _TEXT})
    assert fields["n_key_phrases"] >= 3
    assert isinstance(fields["key_phrases"], list)
    assert "[A]" in fields["key_phrases_text"]
    assert "|" in fields["top_terms"] or fields["top_terms"]


def test_keyphrase_fields_empty_text_is_safe():
    fields = keyphrase_fields({})
    assert fields["n_key_phrases"] == 0
    assert fields["key_phrases"] == []
    assert fields["top_terms"] == ""


def test_extract_keyphrases_from_pages_records_page_number():
    pages = [
        "An introduction with no dietary content whatsoever here.",
        "This guideline recommends increasing fruit and vegetable intake for diet quality.",
        "Families should share meals together to strengthen commensality.",
    ]
    phrases = extract_keyphrases_from_pages(pages)
    a = [p for p in phrases if p["domain"] == "A"][0]
    c = [p for p in phrases if p["domain"] == "C"][0]
    assert a["page"] == 2       # the A sentence is on page 2
    assert c["page"] == 3       # the C sentence is on page 3
    assert "fruit and vegetable" in a["sentence"].lower()
