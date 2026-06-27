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


def test_keyword_taxonomy_supplement_appends_nutrition_social_prescribing_terms(
    tmp_path: Path,
) -> None:
    taxonomy = tmp_path / "keyword_taxonomy.json"
    supplement = tmp_path / "keyword_taxonomy_supplement_food_as_medicine_access.json"
    taxonomy.write_text(
        json.dumps(
            {
                "global": {
                    "implementation_behavior": {
                        "contextual": ["food is medicine referral"]
                    }
                },
                "workstreams": {"busca1": {"web_query_hints": []}},
            }
        ),
        encoding="utf-8",
    )
    supplement.write_text(
        json.dumps(
            {
                "global": {
                    "implementation_behavior": {
                        "contextual": [
                            "nutrition social prescribing",
                            "food social prescribing",
                            "food is medicine referral",
                        ]
                    }
                },
                "workstreams": {
                    "busca1": {
                        "web_query_hints": [
                            "social prescribing food pharmacy",
                            "social prescribing nutrition security",
                        ]
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    loaded = load_json(taxonomy)

    contextual = loaded["global"]["implementation_behavior"]["contextual"]
    hints = loaded["workstreams"]["busca1"]["web_query_hints"]
    assert contextual == [
        "food is medicine referral",
        "nutrition social prescribing",
        "food social prescribing",
    ]
    assert "social prescribing food pharmacy" in hints
    assert "social prescribing nutrition security" in hints


def test_other_json_files_do_not_load_keyword_taxonomy_supplement(tmp_path: Path) -> None:
    config = tmp_path / "scoring_rules.json"
    supplement = tmp_path / "keyword_taxonomy_supplement.json"
    config.write_text(json.dumps({"keyword_points": {"obesity": 2}}), encoding="utf-8")
    supplement.write_text(json.dumps({"keyword_points": {"meal timing": 2}}), encoding="utf-8")

    assert load_json(config) == {"keyword_points": {"obesity": 2}}
