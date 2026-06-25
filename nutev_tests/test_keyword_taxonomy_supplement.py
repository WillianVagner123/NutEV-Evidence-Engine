from __future__ import annotations

import json
from pathlib import Path

from nutev.settings import load_json


ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_PATH = ROOT / "config" / "keyword_taxonomy.json"


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
    supplement.write_text(json.dumps({"keyword_points": {"meal timing": 2}}), encoding="utf-8")

    assert load_json(config) == {"keyword_points": {"obesity": 2}}


def test_a3_instrument_supplement_merges_into_taxonomy() -> None:
    taxonomy = load_json(TAXONOMY_PATH)

    framework = taxonomy["workstreams"]["artigo3_framework"]
    assert "dietary adherence questionnaire" in framework["condition_terms"]
    assert "commensality scale validation" in framework["web_query_hints"]

    behavioral_terms = taxonomy["outcomes"]["behavioral"]
    assert "cooking self-efficacy scale" in behavioral_terms
    assert "family meals scale" in behavioral_terms

    implementation_blocks = taxonomy["global"]["implementation_behavior"]
    assert "adherence_instruments" in implementation_blocks
    assert "dietary adherence scale" in implementation_blocks["adherence_instruments"]
