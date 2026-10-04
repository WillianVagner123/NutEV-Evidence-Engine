"""Term matching policy v2 (audit finding A11): whole word or phrase, optional plural.

Substring matching counted "iron" inside "environment", "fat" inside "fatigue" and
"reach" inside "research". The Open Evidence Explorer port is compared with this
implementation by nutev_tests/test_open_explorer.py.
"""

from __future__ import annotations

from tools.rank_references import TERM_MATCH_POLICY, _has_term, _norm, score_record


def padded(text: str) -> str:
    return f" {_norm(text)} "


def test_substrings_inside_other_words_do_not_match() -> None:
    text = padded("Environmental fatigue research with eggplant")
    for term in ("iron", "fat", "reach", "egg"):
        assert not _has_term(text, term), term


def test_whole_words_phrases_and_plurals_match() -> None:
    text = padded("Dietary fats, iron and eggs in clinical practice guidelines; nutritional therapies")
    for term in ("iron", "fat", "egg", "clinical practice guideline", "therapy", "dietary"):
        assert _has_term(text, term), term
    assert not _has_term(text, "diet")  # "dietary" is its own word, not a plural of "diet"
    assert not _has_term(padded(""), "iron") and not _has_term(text, "")


def test_score_record_uses_the_policy_for_taxonomy_focus_and_document_type() -> None:
    taxonomy = {"nutrient.iron": ["iron"], "nutrient.fat": ["fat"], "framework.reach": ["reach"]}
    row = {
        "title": "Environmental fatigue research: a clinical practice guidelines update",
        "abstract": "",
        "source_provider": "openalex",
        "doi": "10.1/x",
    }
    scored = score_record(row, taxonomy, ["iron"], {})
    assert scored["score_breakdown"]["taxonomy"] == 0
    assert scored["score_breakdown"]["focus_keywords"] == 0
    assert scored["document_type_applied"] == "clinical practice guideline"

    hit = score_record({**row, "title": "Iron and fats in diets"}, taxonomy, ["iron"], {})
    assert hit["score_breakdown"]["taxonomy"] > 0 and hit["score_breakdown"]["focus_keywords"] > 0
    assert TERM_MATCH_POLICY == "nutev-term-match-v2-whole-word-plural"
