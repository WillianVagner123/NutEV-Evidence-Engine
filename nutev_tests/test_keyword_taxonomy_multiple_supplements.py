from __future__ import annotations

import json
from pathlib import Path

from nutev.settings import load_json


def test_keyword_taxonomy_loads_named_supplement_files(tmp_path: Path) -> None:
    taxonomy = tmp_path / "keyword_taxonomy.json"
    exact_supplement = tmp_path / "keyword_taxonomy_supplement.json"
    named_supplement = tmp_path / "keyword_taxonomy_supplement_diet_quality.json"
    taxonomy.write_text(
        json.dumps({"global": {"diet_patterns": {"core": ["dietary pattern"]}}}),
        encoding="utf-8",
    )
    exact_supplement.write_text(
        json.dumps(
            {"global": {"diet_patterns": {"chrononutrition": ["meal timing"]}}}
        ),
        encoding="utf-8",
    )
    named_supplement.write_text(
        json.dumps(
            {
                "global": {
                    "diet_patterns": {
                        "diet_quality_scores": ["healthy eating index"]
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    loaded = load_json(taxonomy)

    assert loaded["global"]["diet_patterns"]["core"] == ["dietary pattern"]
    assert loaded["global"]["diet_patterns"]["chrononutrition"] == ["meal timing"]
    assert loaded["global"]["diet_patterns"]["diet_quality_scores"] == [
        "healthy eating index"
    ]
