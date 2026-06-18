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


def test_keyword_taxonomy_supplement_appends_ckm_workstream_terms(
    tmp_path: Path,
) -> None:
    taxonomy = tmp_path / "keyword_taxonomy.json"
    supplement = tmp_path / "keyword_taxonomy_supplement.json"
    taxonomy.write_text(
        json.dumps(
            {
                "clinical": {"cvd": ["cardiovascular disease"]},
                "workstreams": {
                    "busca2a": {
                        "condition_terms": ["cardiometabolic risk"],
                        "clinical_keys": ["cvd"],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    supplement.write_text(
        json.dumps(
            {
                "clinical": {
                    "cardiovascular_kidney_metabolic": [
                        "cardiovascular-kidney-metabolic syndrome",
                        "ckm syndrome",
                    ]
                },
                "workstreams": {
                    "busca2a": {
                        "condition_terms": [
                            "cardiovascular-kidney-metabolic syndrome",
                            "ckm syndrome",
                        ],
                        "clinical_keys": ["cardiovascular_kidney_metabolic"],
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    loaded = load_json(taxonomy)

    assert loaded["clinical"]["cardiovascular_kidney_metabolic"] == [
        "cardiovascular-kidney-metabolic syndrome",
        "ckm syndrome",
    ]
    assert loaded["workstreams"]["busca2a"]["condition_terms"] == [
        "cardiometabolic risk",
        "cardiovascular-kidney-metabolic syndrome",
        "ckm syndrome",
    ]
    assert loaded["workstreams"]["busca2a"]["clinical_keys"] == [
        "cvd",
        "cardiovascular_kidney_metabolic",
    ]


def test_other_json_files_do_not_load_keyword_taxonomy_supplement(tmp_path: Path) -> None:
    config = tmp_path / "scoring_rules.json"
    supplement = tmp_path / "keyword_taxonomy_supplement.json"
    config.write_text(json.dumps({"keyword_points": {"obesity": 2}}), encoding="utf-8")
    supplement.write_text(json.dumps({"keyword_points": {"meal timing": 2}}), encoding="utf-8")

    assert load_json(config) == {"keyword_points": {"obesity": 2}}
