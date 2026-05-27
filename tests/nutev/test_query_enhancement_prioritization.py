from __future__ import annotations

import json
from pathlib import Path

from nutev.querypacks.builders import build_structured_components


def _load_keyword_taxonomy() -> dict:
    repo_root = Path(__file__).resolve().parents[2]
    return json.loads(
        (repo_root / "config" / "keyword_taxonomy.json").read_text(encoding="utf-8")
    )


def test_busca1_food_as_medicine_expansions_are_prioritized() -> None:
    taxonomy = _load_keyword_taxonomy()
    _, components = build_structured_components(taxonomy, "busca1")

    assert "food as medicine intervention" in components["focus_terms"][:20]
    assert "produce rx" in components["focus_terms"][:20]
    assert "fruit and vegetable prescription" in components["web_hints"][:15]
    assert "healthy food prescription" in components["web_hints"][:15]


def test_busca2b_targeted_food_is_medicine_terms_precede_default_hints() -> None:
    taxonomy = _load_keyword_taxonomy()
    _, components = build_structured_components(taxonomy, "busca2b")

    assert components["focus_terms"].index("food as medicine intervention") < components["focus_terms"].index("lifestyle medicine")
    assert components["focus_terms"].index("produce rx") < components["focus_terms"].index("nutrition")
    assert components["web_hints"].index("fruit and vegetable prescription") < components["web_hints"].index("network meta-analysis")
    assert components["web_hints"].index("healthy food prescription") < components["web_hints"].index("umbrella review")
