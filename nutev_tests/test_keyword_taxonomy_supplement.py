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


def test_scoring_rules_supplement_merges_keyword_and_workstream_terms(
    tmp_path: Path,
) -> None:
    scoring_rules = tmp_path / "scoring_rules.json"
    supplement = tmp_path / "scoring_rules_supplement.json"
    scoring_rules.write_text(
        json.dumps(
            {
                "keyword_points": {"obesity": 2},
                "workstream_bonus": {"busca2a": {"obesity": 3}},
            }
        ),
        encoding="utf-8",
    )
    supplement.write_text(
        json.dumps(
            {
                "version_note": "ignored during merge",
                "keyword_points": {"obesity management guideline": 4},
                "workstream_bonus": {
                    "busca2a": {"obesity management guideline": 5}
                },
            }
        ),
        encoding="utf-8",
    )

    loaded = load_json(scoring_rules)

    assert loaded["keyword_points"]["obesity"] == 2
    assert loaded["keyword_points"]["obesity management guideline"] == 4
    assert loaded["workstream_bonus"]["busca2a"]["obesity"] == 3
    assert loaded["workstream_bonus"]["busca2a"]["obesity management guideline"] == 5
    assert "version_note" not in loaded


def test_other_json_files_do_not_load_keyword_taxonomy_supplement(tmp_path: Path) -> None:
    config = tmp_path / "scoring_rules.json"
    supplement = tmp_path / "keyword_taxonomy_supplement.json"
    config.write_text(json.dumps({"keyword_points": {"obesity": 2}}), encoding="utf-8")
    supplement.write_text(json.dumps({"keyword_points": {"meal timing": 2}}), encoding="utf-8")

    assert load_json(config) == {"keyword_points": {"obesity": 2}}
