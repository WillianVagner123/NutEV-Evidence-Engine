from __future__ import annotations

import json
from pathlib import Path

from nutev.querypacks.provider_queries import render_queries_for_provider
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


def test_food_access_supplement_terms_render_in_provider_queries() -> None:
    taxonomy = load_json(Path("config") / "keyword_taxonomy.json")

    busca1_queries = render_queries_for_provider(taxonomy, "busca1", "openalex")
    busca2b_queries = render_queries_for_provider(taxonomy, "busca2b", "openalex")
    rendered_busca1 = "\n".join(busca1_queries).lower()
    rendered_busca2b = "\n".join(busca2b_queries).lower()

    assert "healthy food box" in rendered_busca1
    assert "food farmacy" in rendered_busca1
    assert "screen and intervene" in rendered_busca1
    assert "food affordability" in rendered_busca1
    assert "produce prescription randomized trial" in rendered_busca2b
    assert "food insecurity intervention cardiometabolic trial" in rendered_busca2b
