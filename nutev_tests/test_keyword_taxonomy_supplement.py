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


def test_keyword_taxonomy_supplement_appends_nutrition_prescription_terms(
    tmp_path: Path,
) -> None:
    taxonomy = tmp_path / "keyword_taxonomy.json"
    supplement = tmp_path / "keyword_taxonomy_supplement.json"
    taxonomy.write_text(
        json.dumps(
            {
                "global": {"nutrition_domains": {"core": ["nutrition"]}},
                "workstreams": {"busca2b": {"focus_terms": ["dietary adherence"]}},
            }
        ),
        encoding="utf-8",
    )
    supplement.write_text(
        json.dumps(
            {
                "global": {
                    "nutrition_domains": {
                        "nutrition_prescription_planning": [
                            "nutrition prescription",
                            "dietary prescription",
                        ]
                    }
                },
                "workstreams": {
                    "busca2b": {
                        "focus_terms": [
                            "nutrition prescription",
                            "personalized meal planning",
                        ]
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    loaded = load_json(taxonomy)

    assert loaded["global"]["nutrition_domains"]["core"] == ["nutrition"]
    assert loaded["global"]["nutrition_domains"]["nutrition_prescription_planning"] == [
        "nutrition prescription",
        "dietary prescription",
    ]
    assert loaded["workstreams"]["busca2b"]["focus_terms"] == [
        "dietary adherence",
        "nutrition prescription",
        "personalized meal planning",
    ]


def test_other_json_files_do_not_load_keyword_taxonomy_supplement(tmp_path: Path) -> None:
    config = tmp_path / "scoring_rules.json"
    supplement = tmp_path / "keyword_taxonomy_supplement.json"
    config.write_text(json.dumps({"keyword_points": {"obesity": 2}}), encoding="utf-8")
    supplement.write_text(json.dumps({"keyword_points": {"meal timing": 2}}), encoding="utf-8")

    assert load_json(config) == {"keyword_points": {"obesity": 2}}
