from __future__ import annotations

import json
from pathlib import Path

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


def test_keyword_taxonomy_loads_ordered_additional_supplements(tmp_path: Path) -> None:
    taxonomy = tmp_path / "keyword_taxonomy.json"
    base_supplement = tmp_path / "keyword_taxonomy_supplement.json"
    extra_supplement = tmp_path / "keyword_taxonomy_supplement_food_competence.json"
    taxonomy.write_text(
        json.dumps({"workstreams": {"artigo3_framework": {"focus_terms": ["food literacy"]}}}),
        encoding="utf-8",
    )
    base_supplement.write_text(
        json.dumps({"workstreams": {"artigo3_framework": {"focus_terms": ["eating competence"]}}}),
        encoding="utf-8",
    )
    extra_supplement.write_text(
        json.dumps({"workstreams": {"artigo3_framework": {"focus_terms": ["home food availability"]}}}),
        encoding="utf-8",
    )

    loaded = load_json(taxonomy)

    assert loaded["workstreams"]["artigo3_framework"]["focus_terms"] == [
        "food literacy",
        "eating competence",
        "home food availability",
    ]


def test_other_json_files_do_not_load_keyword_taxonomy_supplement(tmp_path: Path) -> None:
    config = tmp_path / "scoring_rules.json"
    supplement = tmp_path / "keyword_taxonomy_supplement.json"
    config.write_text(json.dumps({"keyword_points": {"obesity": 2}}), encoding="utf-8")
    supplement.write_text(json.dumps({"keyword_points": {"meal timing": 2}}), encoding="utf-8")

    assert load_json(config) == {"keyword_points": {"obesity": 2}}
