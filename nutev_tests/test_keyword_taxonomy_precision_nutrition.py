import json
from pathlib import Path

from nutev.querypacks.builders import build_querypack


def _render_querypack(workstreams: list[str]) -> str:
    taxonomy = json.loads(Path("config/keyword_taxonomy.json").read_text(encoding="utf-8"))
    querypack = build_querypack(taxonomy, workstreams)
    return " ".join(
        query.lower()
        for queries in querypack.values()
        for query in queries
    )


def test_busca2b_querypack_includes_precision_nutrition_intervention_terms():
    rendered = _render_querypack(["busca2b"])

    assert "personalized nutrition" in rendered
    assert "precision nutrition" in rendered
    assert "tailored dietary intervention" in rendered
    assert "individualized dietary intervention" in rendered


def test_artigo3_querypack_includes_precision_nutrition_framework_terms():
    rendered = _render_querypack(["artigo3_framework"])

    assert "personalized nutrition" in rendered
    assert "precision nutrition" in rendered
    assert "tailored nutrition framework" in rendered
