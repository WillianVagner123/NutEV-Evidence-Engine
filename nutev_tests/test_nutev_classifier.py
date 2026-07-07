from __future__ import annotations

from nutev.analysis.nutev_classifier import classify_evidence


def test_classify_evidence_uses_term_boundaries() -> None:
    records = [
        {
            "title": "Reminder system for routine visits",
            "abstract": "A dashboard improved scheduling, but did not evaluate diet quality.",
        }
    ]
    ontology = {
        "domains": {
            "diet_patterns": ["mind", "dash", "diet"],
            "implementation": ["implementation"],
        },
        "outcomes": {
            "adherence": ["adherence"],
        },
    }
    lenses_cfg = {"lenses": {"nutrition": {"domains": ["diet_patterns"]}}}

    [classified] = classify_evidence(records, ontology, lenses_cfg)

    assert classified["domain_diet_patterns_count"] == 1
    assert classified["domain_diet_patterns_present"] == 1
    assert classified["domain_implementation_count"] == 0
    assert classified["outcome_adherence_count"] == 0
    assert classified["domains"] == ["diet_patterns"]
    assert classified["evidence_lenses"] == ["nutrition"]


def test_classify_evidence_matches_hyphenated_and_phrase_terms() -> None:
    records = [
        {
            "title": "Food-based dietary guideline for adults",
            "abstract": "A plant-based diet pattern improved adherence.",
        }
    ]
    ontology = {
        "domains": {
            "guidelines": ["food-based dietary guideline"],
            "diet_patterns": ["plant-based diet"],
        },
        "outcomes": {"adherence": ["adherence"]},
    }
    lenses_cfg = {"lenses": {}}

    [classified] = classify_evidence(records, ontology, lenses_cfg)

    assert classified["domain_guidelines_count"] == 1
    assert classified["domain_diet_patterns_count"] == 1
    assert classified["outcome_adherence_count"] == 1
    assert classified["domains"] == ["diet_patterns", "guidelines"]
