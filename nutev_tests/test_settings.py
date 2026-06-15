from __future__ import annotations

import json
from pathlib import Path

from nutev.settings import load_json


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def test_load_json_merges_primary_and_versioned_supplements(tmp_path: Path) -> None:
    config = tmp_path / "keyword_taxonomy.json"
    primary = tmp_path / "keyword_taxonomy_supplement.json"
    versioned = tmp_path / "keyword_taxonomy_supplement_social_prescribing.json"

    _write_json(
        config,
        {
            "global": {
                "implementation_behavior": {
                    "food_as_medicine_access": ["food is medicine"]
                }
            }
        },
    )
    _write_json(
        primary,
        {
            "version_note": "ignored metadata",
            "global": {
                "implementation_behavior": {
                    "food_as_medicine_access": ["produce prescription"]
                }
            },
        },
    )
    _write_json(
        versioned,
        {
            "global": {
                "implementation_behavior": {
                    "food_as_medicine_access": [
                        "produce prescription",
                        "nutrition-sensitive social prescribing",
                    ]
                }
            }
        },
    )

    loaded = load_json(config)

    terms = loaded["global"]["implementation_behavior"]["food_as_medicine_access"]
    assert terms == [
        "food is medicine",
        "produce prescription",
        "nutrition-sensitive social prescribing",
    ]
    assert "version_note" not in loaded
