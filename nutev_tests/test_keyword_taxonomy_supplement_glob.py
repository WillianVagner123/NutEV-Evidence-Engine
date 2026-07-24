from __future__ import annotations

import json
from pathlib import Path

from nutev.settings import load_json


def test_keyword_taxonomy_loads_named_supplement_globs(tmp_path: Path) -> None:
    taxonomy = tmp_path / "keyword_taxonomy.json"
    first = tmp_path / "keyword_taxonomy_supplement.json"
    second = tmp_path / "keyword_taxonomy_supplement_anti_obesity_nutrition.json"
    taxonomy.write_text(
        json.dumps({"global": {"implementation_behavior": {"core": ["adherence"]}}}),
        encoding="utf-8",
    )
    first.write_text(
        json.dumps({"global": {"implementation_behavior": {"core": ["implementation"]}}}),
        encoding="utf-8",
    )
    second.write_text(
        json.dumps(
            {
                "global": {
                    "implementation_behavior": {
                        "anti_obesity_nutrition_care": [
                            "anti-obesity medication nutrition"
                        ]
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    loaded = load_json(taxonomy)

    assert loaded["global"]["implementation_behavior"]["core"] == [
        "adherence",
        "implementation",
    ]
    assert loaded["global"]["implementation_behavior"][
        "anti_obesity_nutrition_care"
    ] == ["anti-obesity medication nutrition"]
