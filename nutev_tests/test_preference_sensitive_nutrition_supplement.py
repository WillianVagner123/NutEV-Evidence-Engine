from __future__ import annotations

import json
from pathlib import Path

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.settings import load_json


def test_preference_sensitive_nutrition_supplement_loads_into_taxonomy() -> None:
    taxonomy = load_json(Path(__file__).resolve().parents[1] / "config" / "keyword_taxonomy.json")

    terms = taxonomy["global"]["implementation_behavior"]["preference_sensitive_nutrition"]
    busca2b_hints = taxonomy["workstreams"]["busca2b"]["web_query_hints"]

    assert "preference-sensitive nutrition" in terms
    assert "patient-centered nutrition" in terms
    assert "personalized nutrition cardiometabolic trial" in busca2b_hints


def test_preference_sensitive_terms_are_rendered_in_busca2b_provider_queries() -> None:
    taxonomy = json.loads(
        (Path(__file__).resolve().parents[1] / "config" / "keyword_taxonomy.json").read_text(
            encoding="utf-8"
        )
    )
    supplement = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "config"
            / "keyword_taxonomy_supplement_20260713_preference_sensitive_nutrition.json"
        ).read_text(encoding="utf-8")
    )
    taxonomy["global"]["implementation_behavior"].update(
        supplement["global"]["implementation_behavior"]
    )
    taxonomy["workstreams"]["busca2b"]["web_query_hints"].extend(
        supplement["workstreams"]["busca2b"]["web_query_hints"]
    )

    queries = render_queries_for_provider(taxonomy, "busca2b", "pubmed")
    joined = "\n".join(queries)

    assert '"preference-sensitive nutrition"[Title/Abstract]' in joined
    assert '"patient-centered nutrition"[Title/Abstract]' in joined
    assert '"tailored dietary intervention"[Title/Abstract]' in joined
