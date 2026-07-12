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


def test_other_json_files_do_not_load_keyword_taxonomy_supplement(tmp_path: Path) -> None:
    config = tmp_path / "scoring_rules.json"
    supplement = tmp_path / "keyword_taxonomy_supplement.json"
    config.write_text(json.dumps({"keyword_points": {"obesity": 2}}), encoding="utf-8")
    supplement.write_text(
        json.dumps({"keyword_points": {"meal timing": 2}}),
        encoding="utf-8",
    )

    assert load_json(config) == {"keyword_points": {"obesity": 2}}


def test_cardiorenal_scoring_supplement_adds_ckm_syndrome_terms(tmp_path: Path) -> None:
    scoring = tmp_path / "scoring_rules.json"
    supplement = tmp_path / "scoring_rules_supplement_cardiorenal.json"
    scoring.write_text(
        json.dumps(
            {
                "keyword_points": {"cardiometabolic risk": 2},
                "workstream_bonus": {"busca2a": {"cardiometabolic risk": 3}},
            }
        ),
        encoding="utf-8",
    )
    supplement.write_text(
        json.dumps(
            {
                "keyword_points": {
                    "cardiovascular-kidney-metabolic syndrome": 3,
                    "cardiovascular kidney metabolic syndrome": 3,
                    "ckm syndrome": 3,
                },
                "workstream_bonus": {
                    "busca2a": {
                        "cardiovascular-kidney-metabolic syndrome": 5,
                        "cardiovascular kidney metabolic syndrome": 5,
                        "ckm syndrome": 5,
                    },
                    "busca2b": {
                        "cardiovascular-kidney-metabolic syndrome": 5,
                        "cardiovascular kidney metabolic syndrome": 5,
                        "ckm syndrome": 5,
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    loaded = load_json(scoring)

    assert loaded["keyword_points"]["cardiovascular-kidney-metabolic syndrome"] == 3
    assert loaded["keyword_points"]["cardiovascular kidney metabolic syndrome"] == 3
    assert loaded["keyword_points"]["ckm syndrome"] == 3
    assert loaded["workstream_bonus"]["busca2a"]["ckm syndrome"] == 5
    assert loaded["workstream_bonus"]["busca2b"]["ckm syndrome"] == 5
