from __future__ import annotations

import json
from pathlib import Path

from nutev.querypacks.builders import build_structured_components
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
    supplement.write_text(json.dumps({"keyword_points": {"meal timing": 2}}), encoding="utf-8")

    assert load_json(config) == {"keyword_points": {"obesity": 2}}


def _components_for(workstream: str) -> dict[str, list[str]]:
    taxonomy = load_json(Path("config/keyword_taxonomy.json"))
    _, components = build_structured_components(taxonomy, workstream)
    return components


def test_masld_nutrition_terms_expand_busca2a_guideline_queries() -> None:
    components = _components_for("busca2a")

    assert "MASLD nutrition" in components["condition_terms"]
    assert "MASLD clinical practice guideline" in components["web_hints"]
    assert "steatotic liver disease practice guidance" in components["web_hints"]


def test_masld_nutrition_terms_expand_busca2b_intervention_queries() -> None:
    components = _components_for("busca2b")

    assert "MASLD dietary intervention" in components["condition_terms"]
    assert "MASLD lifestyle intervention" in components["focus_terms"]
    assert "MASLD nutrition systematic review" in components["web_hints"]
    assert "lifestyle intervention trial" in components["doc_type_terms"]
