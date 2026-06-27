from __future__ import annotations

import sitecustomize  # noqa: F401

from nutev.querypacks.builders import build_queries
from nutev.querypacks.provider_queries import render_queries_for_provider


def test_busca2a_pubmed_queries_include_personalized_nutrition_anchors() -> None:
    rendered = "\n".join(render_queries_for_provider({}, "busca2a", "pubmed")).lower()

    assert '"personalized nutrition guideline"[title/abstract]' in rendered
    assert '"precision nutrition type 2 diabetes"[title/abstract]' in rendered
    assert '"tailored dietary advice cardiometabolic risk"[title/abstract]' in rendered
    assert '"individualized dietary intervention type 2 diabetes"[title/abstract]' in rendered


def test_busca2b_structured_queries_anchor_personalized_nutrition_to_nutmev_scope() -> None:
    rendered = "\n".join(build_queries({}, "busca2b")).lower()

    assert '"personalized nutrition"' in rendered
    assert '"precision nutrition"' in rendered
    assert '"tailored dietary advice"' in rendered
    assert '"obesity" or "type 2 diabetes" or "cardiometabolic risk"' in rendered
