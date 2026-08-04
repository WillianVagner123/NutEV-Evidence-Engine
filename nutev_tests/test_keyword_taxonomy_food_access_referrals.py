from __future__ import annotations

import json
from pathlib import Path


def _supplement() -> dict:
    path = Path("config") / "keyword_taxonomy_supplement.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_food_access_referral_terms_are_in_global_taxonomy() -> None:
    taxonomy = _supplement()
    access_terms = set(
        taxonomy["global"]["implementation_behavior"]["food_as_medicine_access"]
    )
    outcome_terms = set(taxonomy["outcomes"]["food_access_implementation"])

    expected_terms = {
        "produce prescription referral",
        "food pharmacy implementation",
        "food pharmacy referral",
        "food farmacy implementation",
        "food farmacy referral",
        "medically tailored meals referral",
        "medically tailored grocery referral",
        "medically tailored food referral",
    }

    assert expected_terms <= access_terms
    assert expected_terms <= outcome_terms


def test_food_access_referral_terms_are_workstream_scoped() -> None:
    taxonomy = _supplement()
    busca1_terms = set(taxonomy["workstreams"]["busca1"]["focus_terms"])
    busca2b_terms = set(taxonomy["workstreams"]["busca2b"]["focus_terms"])
    busca1_hints = "\n".join(taxonomy["workstreams"]["busca1"]["web_query_hints"])
    busca2b_hints = "\n".join(taxonomy["workstreams"]["busca2b"]["web_query_hints"])

    expected_terms = {
        "produce prescription referral",
        "food pharmacy implementation",
        "food farmacy implementation",
        "medically tailored food referral",
    }

    assert expected_terms <= busca1_terms
    assert expected_terms <= busca2b_terms
    assert "food pharmacy implementation report" in busca1_hints
    assert "food farmacy implementation trial" in busca2b_hints
    assert "medically tailored grocery referral program" in busca2b_hints
