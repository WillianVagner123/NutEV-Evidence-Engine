from __future__ import annotations

import json
from pathlib import Path

from nutev.querypacks.builders import build_structured_components


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_keyword_taxonomy() -> dict:
    with (REPO_ROOT / "config" / "keyword_taxonomy.json").open(encoding="utf-8") as handle:
        return json.load(handle)


def _missing_terms(values: list[str], expected_terms: set[str]) -> set[str]:
    normalized_values = {str(value).lower() for value in values}
    return {term for term in expected_terms if term.lower() not in normalized_values}


def test_busca2b_keeps_metabolic_remission_and_implementation_terms() -> None:
    _, components = build_structured_components(_load_keyword_taxonomy(), "busca2b")

    expected_focus_terms = {
        "diabetes remission",
        "type 2 diabetes remission",
        "weight loss maintenance",
        "long-term weight loss maintenance",
        "weight regain prevention",
        "food is medicine",
        "produce prescription",
        "medically tailored meals",
        "social prescribing",
        "dietitian-led intervention",
        "registered dietitian nutritionist-led intervention",
    }
    expected_document_terms = {
        "remission consensus report",
        "remission guideline",
        "weight loss maintenance trial",
        "weight loss maintenance systematic review",
    }
    expected_web_hints = {
        "diabetes remission guideline",
        "type 2 diabetes remission consensus",
        "weight regain prevention trial",
        "closed-loop referral",
        "community health worker-led nutrition",
    }

    missing = {
        "focus_terms": _missing_terms(components["focus_terms"], expected_focus_terms),
        "doc_type_terms": _missing_terms(components["doc_type_terms"], expected_document_terms),
        "web_hints": _missing_terms(components["web_hints"], expected_web_hints),
    }

    assert not {group: terms for group, terms in missing.items() if terms}
