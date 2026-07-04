from __future__ import annotations

import json
from pathlib import Path

from nutev.querypacks.builders import build_structured_components
from nutev.settings import load_json


def test_keyword_taxonomy_supplement_appends_chrononutrition_terms(tmp_path: Path) -> None:
    taxonomy = tmp_path / "keyword_taxonomy.json"
    supplement = tmp_path / "keyword_taxonomy_supplement.json"
    taxonomy.write_text(
        json.dumps({"global": {"diet_patterns": {"core": ["dietary pattern"]}}}),
        encoding="utf-8",
    )
    supplement.write_text(
        json.dumps(
            {
                "global": {
                    "diet_patterns": {
                        "chrononutrition": ["chrononutrition", "meal timing"]
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    loaded = load_json(taxonomy)

    assert loaded["global"]["diet_patterns"]["core"] == ["dietary pattern"]
    assert loaded["global"]["diet_patterns"]["chrononutrition"] == [
        "chrononutrition",
        "meal timing",
    ]


def test_keyword_taxonomy_loads_suffixed_supplements(tmp_path: Path) -> None:
    taxonomy = tmp_path / "keyword_taxonomy.json"
    supplement = tmp_path / "keyword_taxonomy_supplement_cardiometabolic.json"
    taxonomy.write_text(
        json.dumps({"clinical": {"cardiometabolic": ["cardiometabolic risk"]}}),
        encoding="utf-8",
    )
    supplement.write_text(
        json.dumps({"clinical": {"cardiometabolic": ["chronic kidney disease"]}}),
        encoding="utf-8",
    )

    loaded = load_json(taxonomy)

    assert loaded["clinical"]["cardiometabolic"] == [
        "cardiometabolic risk",
        "chronic kidney disease",
    ]


def test_real_keyword_taxonomy_supplements_surface_ckm_kidney_terms() -> None:
    taxonomy = load_json(
        Path(__file__).resolve().parents[1] / "config" / "keyword_taxonomy.json"
    )

    _, busca2a_components = build_structured_components(taxonomy, "busca2a")
    _, busca2b_components = build_structured_components(taxonomy, "busca2b")

    assert "chronic kidney disease" in taxonomy["clinical"]["cardiometabolic"]
    assert "albuminuria" in taxonomy["outcomes"]["cardiometabolic"]
    assert "chronic kidney disease" in busca2a_components["condition_terms"]
    assert "egfr" in busca2b_components["condition_terms"]
    assert any(
        "ckm syndrome kidney" in hint.lower()
        for hint in busca2a_components["web_hints"] + busca2b_components["web_hints"]
    )


def test_other_json_files_do_not_load_keyword_taxonomy_supplement(tmp_path: Path) -> None:
    config = tmp_path / "scoring_rules.json"
    supplement = tmp_path / "keyword_taxonomy_supplement.json"
    config.write_text(json.dumps({"keyword_points": {"obesity": 2}}), encoding="utf-8")
    supplement.write_text(json.dumps({"keyword_points": {"meal timing": 2}}), encoding="utf-8")

    assert load_json(config) == {"keyword_points": {"obesity": 2}}
