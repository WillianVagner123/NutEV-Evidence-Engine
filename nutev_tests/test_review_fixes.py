"""Regression tests for bugs found in the code review."""

from __future__ import annotations

from nutev.analysis.enrich_geo import country_from_text, enrich_record, normalize_language
from nutev.export.knowledge_base import to_kb_record
from nutev.querypacks.multilingual import active_concepts
from nutev.search.crossref import _crossref_date_parts, _normalize_crossref


# --- Crossref empty date-parts no longer raises / aborts the query ---------
def test_crossref_empty_date_parts_does_not_crash():
    assert _crossref_date_parts({"published-online": {"date-parts": [[]]}}) == []
    rec = _normalize_crossref({"published-online": {"date-parts": [[]]}, "title": ["x"]}, "q")
    assert rec["year"] == "" and rec["publication_date"] == ""


def test_crossref_normal_date_parts():
    assert _crossref_date_parts({"published-print": {"date-parts": [[2021, 5]]}}) == [2021, 5]
    rec = _normalize_crossref({"published-print": {"date-parts": [[2021, 5]]}, "title": ["x"]}, "q")
    assert rec["year"] == "2021" and rec["publication_date"] == "2021-5"


# --- Language codes normalized to ISO-639-1 (PubMed 'eng' == OpenAlex 'en') --
def test_normalize_language():
    assert normalize_language("eng") == "en"
    assert normalize_language("POR") == "pt"
    assert normalize_language("en-US") == "en"
    assert normalize_language("") == ""


def test_enrich_record_normalizes_pubmed_language():
    out = enrich_record({"language": "eng", "title": "t", "abstract": "a"})
    assert out["language"] == "en"


# --- "Georgia" (US state) no longer mis-detected as the country GE ----------
def test_georgia_state_not_country():
    assert country_from_text("Emory University, Atlanta, Georgia, USA") == ["US"]


# --- cited_by_count tolerates float-like strings (no silent data loss) ------
def test_enrich_record_cited_by_count_float_string():
    assert enrich_record({"cited_by_count": "42.0"})["cited_by_count"] == 42
    assert enrich_record({"cited_by_count": "1,234"})["cited_by_count"] == 1234
    assert enrich_record({"cited_by_count": ""})["cited_by_count"] == 0


# --- relevance_score coerced to a number on KB build (symmetry w/ cited) ----
def test_kb_relevance_score_coerced():
    assert to_kb_record({"doi": "d", "relevance_score": "3.5"})["relevance_score"] == 3.5
    assert to_kb_record({"doi": "d", "relevance_score": "5"})["relevance_score"] == 5
    assert to_kb_record({"doi": "d", "relevance_score": ""})["relevance_score"] == 0


# --- multilingual: short tokens no longer activate every concept -----------
def test_active_concepts_ignores_short_tokens():
    lex = {"concepts": {"obesity": {"en": ["obesity"]}}, "concept_groups": {"conditions": ["obesity"]}}
    assert active_concepts(["a", "i"], lex, "conditions") == []  # was: matched everything
    assert active_concepts(["childhood obesity"], lex, "conditions") == ["obesity"]
    assert active_concepts(["obesity"], lex, "conditions") == ["obesity"]
