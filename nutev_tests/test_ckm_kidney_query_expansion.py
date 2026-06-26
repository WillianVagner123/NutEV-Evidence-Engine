from __future__ import annotations

import sitecustomize  # noqa: F401

from nutev.querypacks.builders import build_queries
from nutev.querypacks.provider_queries import render_queries_for_provider


def test_busca2b_build_queries_include_ckm_kidney_nutrition_anchor() -> None:
    rendered = " ".join(build_queries({}, "busca2b")).lower()

    assert "chronic kidney disease" in rendered
    assert "diabetic kidney disease" in rendered
    assert "albuminuria" in rendered
    assert "medical nutrition therapy" in rendered


def test_pubmed_provider_queries_include_ckm_kidney_terms_for_clinical_guidance() -> None:
    busca2a = " ".join(render_queries_for_provider({}, "busca2a", "pubmed")).lower()
    busca2b = " ".join(render_queries_for_provider({}, "busca2b", "pubmed")).lower()

    assert '"chronic kidney disease"[title/abstract]' in busca2a
    assert '"albuminuria"[title/abstract]' in busca2b
