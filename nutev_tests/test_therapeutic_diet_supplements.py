from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_SUPPLEMENT = ROOT / "config" / "keyword_taxonomy_supplement_therapeutic_diets.json"
SCORING_SUPPLEMENT = ROOT / "config" / "scoring_rules_supplement_therapeutic_diets.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_therapeutic_diet_taxonomy_supplement_has_bounded_semantic_blocks() -> None:
    data = _load_json(TAXONOMY_SUPPLEMENT)
    diet_patterns = data["global"]["diet_patterns"]

    assert "therapeutic_weight_loss" in diet_patterns
    assert "carbohydrate_restriction" in diet_patterns
    assert "diet_quality_interventions" in diet_patterns
    assert "total diet replacement" in diet_patterns["therapeutic_weight_loss"]
    assert "low-carbohydrate diet" in diet_patterns["carbohydrate_restriction"]
    assert "structured dietary intervention" in diet_patterns["diet_quality_interventions"]


def test_therapeutic_diet_scoring_supplement_prioritizes_clinical_workstreams() -> None:
    data = _load_json(SCORING_SUPPLEMENT)

    assert data["keyword_points"]["total diet replacement"] >= 4
    assert data["keyword_points"]["low-carbohydrate diet"] >= 3
    assert data["workstream_bonus"]["busca2a"]["very low energy diet guideline"] >= 5
    assert data["workstream_bonus"]["busca2b"]["dietary pattern intervention"] >= 5
