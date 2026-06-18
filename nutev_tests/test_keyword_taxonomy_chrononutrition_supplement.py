from __future__ import annotations

import json
from pathlib import Path

from nutev.settings import load_json


def test_keyword_taxonomy_chrononutrition_supplement_targets_busca2b(
    tmp_path: Path,
) -> None:
    taxonomy = tmp_path / "keyword_taxonomy.json"
    supplement = tmp_path / "keyword_taxonomy_supplement_chrononutrition_adherence.json"
    taxonomy.write_text(
        json.dumps(
            {
                "global": {"diet_patterns": {"core": ["dietary pattern"]}},
                "workstreams": {"busca2b": {"focus_terms": ["adherence"]}},
            }
        ),
        encoding="utf-8",
    )
    supplement.write_text(
        json.dumps(
            {
                "global": {
                    "diet_patterns": {
                        "chrononutrition_adherence": [
                            "chrononutrition adherence",
                            "meal timing adherence",
                        ]
                    }
                },
                "workstreams": {
                    "busca2b": {
                        "focus_terms": [
                            "time-restricted eating adherence",
                            "meal timing intervention",
                        ]
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    loaded = load_json(taxonomy)

    assert loaded["global"]["diet_patterns"]["core"] == ["dietary pattern"]
    assert loaded["global"]["diet_patterns"]["chrononutrition_adherence"] == [
        "chrononutrition adherence",
        "meal timing adherence",
    ]
    assert loaded["workstreams"]["busca2b"]["focus_terms"] == [
        "adherence",
        "time-restricted eating adherence",
        "meal timing intervention",
    ]
