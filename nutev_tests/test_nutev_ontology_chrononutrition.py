from __future__ import annotations

from pathlib import Path

from nutev.settings import load_json


def test_ontology_tracks_chrononutrition_as_dietary_pattern() -> None:
    ontology = load_json(Path("config/nutev_ontology.json"))
    dietary_patterns = {term.lower() for term in ontology["domains"]["dietary_patterns"]}

    assert "chrononutrition" in dietary_patterns
    assert "meal timing" in dietary_patterns
    assert "time-restricted eating" in dietary_patterns
    assert "eating window" in dietary_patterns


def test_ontology_tracks_specific_cardiometabolic_outcomes() -> None:
    ontology = load_json(Path("config/nutev_ontology.json"))
    cardiometabolic = {term.lower() for term in ontology["outcomes"]["cardiometabolic"]}

    assert "glycemia" in cardiometabolic
    assert "hba1c" in cardiometabolic
    assert "waist circumference" in cardiometabolic
    assert "masld" in cardiometabolic
