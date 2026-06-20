import json
from pathlib import Path


def test_nutev_ontology_covers_core_semantic_axes():
    ontology = json.loads(
        (Path(__file__).resolve().parents[2] / "config" / "nutev_ontology.json").read_text(
            encoding="utf-8"
        )
    )

    domains = ontology["domains"]
    outcomes = ontology["outcomes"]
    evidence_types = set(ontology["evidence_types"])

    assert "food_literacy_culinary_medicine" in domains
    assert "food_is_medicine" in domains
    assert "culinary medicine" in domains["food_literacy_culinary_medicine"]
    assert "produce prescription" in domains["food_is_medicine"]

    assert "liver_metabolic" in outcomes
    assert "diet_quality_adherence" in outcomes
    assert "masld" in outcomes["liver_metabolic"]
    assert "dietary adherence" in outcomes["diet_quality_adherence"]

    assert "umbrella review" in evidence_types
    assert "implementation study" in evidence_types
