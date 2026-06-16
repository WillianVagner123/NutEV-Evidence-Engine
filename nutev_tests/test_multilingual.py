from __future__ import annotations

from nutev.querypacks.multilingual import (
    active_concepts,
    concept_terms,
    render_mesh_queries,
    render_multilingual_queries,
)
from nutev.querypacks.provider_queries import _interleave_queries, render_queries_for_provider

LEXICON = {
    "languages": ["en", "pt", "es", "fr", "zh", "ru", "ar"],
    "concept_groups": {
        "conditions": ["type 2 diabetes", "obesity"],
        "diets": ["mediterranean diet"],
        "outcomes": ["glycemic control"],
        "doc_types": ["systematic review"],
    },
    "mesh": {
        "type 2 diabetes": "Diabetes Mellitus, Type 2",
        "mediterranean diet": "Diet, Mediterranean",
        "systematic review": "Systematic Review",
    },
    "concepts": {
        "type 2 diabetes": {
            "en": ["type 2 diabetes"], "pt": ["diabetes tipo 2"], "es": ["diabetes tipo 2"],
            "fr": ["diabète de type 2"], "zh": ["2型糖尿病"], "ru": ["диабет 2 типа"], "ar": ["السكري من النوع الثاني"],
        },
        "obesity": {"en": ["obesity"], "pt": ["obesidade"], "es": ["obesidad"], "fr": ["obésité"], "zh": ["肥胖"], "ru": ["ожирение"], "ar": ["السمنة"]},
        "mediterranean diet": {"en": ["mediterranean diet"], "pt": ["dieta mediterrânea"], "fr": ["régime méditerranéen"], "zh": ["地中海饮食"], "ru": ["средиземноморская диета"], "ar": ["حمية البحر الأبيض المتوسط"]},
        "glycemic control": {"en": ["glycemic control"], "pt": ["controle glicêmico"]},
        "systematic review": {"en": ["systematic review"], "pt": ["revisão sistemática"]},
    },
}

COMPONENTS = {
    "condition_terms": ["type 2 diabetes mellitus", "obesity"],
    "clinical_terms": [],
    "diet_terms": ["mediterranean diet"],
    "nutrition_terms": [],
    "priority_outcomes": ["glycemic control"],
    "doc_type_terms": ["systematic review"],
}


def test_active_concepts_matches_synonyms_loosely():
    matched = active_concepts(["type 2 diabetes mellitus", "obesity"], LEXICON, "conditions")
    assert matched == ["type 2 diabetes", "obesity"]


def test_concept_terms_span_languages():
    terms = concept_terms("type 2 diabetes", LEXICON)
    assert "2型糖尿病" in terms and "diabetes tipo 2" in terms and "السكري من النوع الثاني" in terms


def test_render_multilingual_queries_cover_many_scripts():
    queries = render_multilingual_queries(COMPONENTS, LEXICON, "crossref")
    blob = " || ".join(queries)
    for term in ["diabetes tipo 2", "régime méditerranéen", "2型糖尿病", "средиземноморская диета", "السكري من النوع الثاني"]:
        assert term in blob, term
    # AND-combined condition x (diet/outcome/doctype)
    assert any(" AND " in q for q in queries)


def test_preprints_uses_europepmc_field_syntax():
    queries = render_multilingual_queries(COMPONENTS, LEXICON, "preprints")
    assert any("TITLE_ABS:" in q for q in queries)


def test_pubmed_field_syntax_in_multilingual():
    queries = render_multilingual_queries(COMPONENTS, LEXICON, "pubmed")
    assert any("[Title/Abstract]" in q for q in queries)


def test_render_mesh_queries_language_independent():
    queries = render_mesh_queries(COMPONENTS, LEXICON)
    assert '"Diabetes Mellitus, Type 2"[MeSH Terms]' in queries
    assert any("[Publication Type]" in q for q in queries)


def test_interleave_front_loads_extra():
    base = [f"b{i}" for i in range(100)]
    extra = ["x0", "x1", "x2"]
    woven = _interleave_queries(base, extra)
    assert woven[:6] == ["x0", "b0", "b1", "x1", "b2", "b3"]
    # all extra present within the first budget-sized slice
    assert set(extra) <= set(woven[:36])
    # nothing lost
    assert set(woven) == set(base) | set(extra)


def test_interleave_no_extra_returns_base():
    base = ["a", "b"]
    assert _interleave_queries(base, []) == base


def test_render_queries_for_provider_injects_worldwide_terms():
    tax = {"workstreams": {"busca2b": {"condition_terms": ["type 2 diabetes"], "diet_patterns": ["mediterranean diet"]}}}
    without = render_queries_for_provider(tax, "busca2b", "crossref")
    with_lex = render_queries_for_provider(tax, "busca2b", "crossref", lexicon=LEXICON)
    # lexicon expansion adds non-English content not present in the English-only base
    assert "|| ".join(with_lex) != "|| ".join(without)
    assert any("2型糖尿病" in q for q in with_lex)
