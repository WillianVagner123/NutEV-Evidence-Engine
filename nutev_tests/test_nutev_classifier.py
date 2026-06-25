from __future__ import annotations

from nutev.analysis.nutev_classifier import classify_evidence


def test_classifier_uses_term_boundaries_to_avoid_substring_false_positive():
    records = [
        {
            "title": "Operational dashboard for nutrition program monitoring",
            "abstract": "No dietary pattern is evaluated here.",
        }
    ]
    ontology = {"domains": {"diet_patterns": ["dash"]}, "outcomes": {}}
    lenses = {"lenses": {"nutrition": {"domains": ["diet_patterns"]}}}

    [classified] = classify_evidence(records, ontology, lenses)

    assert classified["domain_diet_patterns_count"] == 0
    assert classified["domain_diet_patterns_present"] == 0
    assert classified["evidence_lenses"] == []


def test_classifier_normalizes_hyphenated_terms_for_relevant_matches():
    records = [
        {
            "title": "Plant based dietary intervention for cardiometabolic risk",
            "abstract": "A nutrition trial with relevant outcomes.",
        }
    ]
    ontology = {
        "domains": {"diet_patterns": ["plant-based"]},
        "outcomes": {"cardiometabolic": ["cardiometabolic risk"]},
    }
    lenses = {"lenses": {"nutrition": {"domains": ["diet_patterns"]}}}

    [classified] = classify_evidence(records, ontology, lenses)

    assert classified["domain_diet_patterns_count"] == 1
    assert classified["outcome_cardiometabolic_count"] == 1
    assert classified["evidence_lenses"] == ["nutrition"]
