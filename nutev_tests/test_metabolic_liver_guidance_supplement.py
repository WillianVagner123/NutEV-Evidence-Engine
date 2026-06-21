from __future__ import annotations

from pathlib import Path

from nutev.querypacks.builders import build_queries, build_structured_components
from nutev.settings import load_json


def test_metabolic_liver_guidance_terms_reach_busca2a_components() -> None:
    taxonomy = load_json(Path("config") / "keyword_taxonomy.json")

    _, components = build_structured_components(taxonomy, "busca2a")
    doc_terms = {term.lower() for term in components["doc_type_terms"]}
    clinical_terms = {term.lower() for term in components["clinical_terms"]}
    web_hints = {term.lower() for term in components["web_hints"]}

    assert "masld practice guidance" in doc_terms
    assert "nafld clinical practice guideline" in doc_terms
    assert "steatotic liver disease practice guidance" in doc_terms
    assert "metabolic dysfunction associated steatotic liver disease" in clinical_terms
    assert "metabolic dysfunction-associated steatohepatitis practice guidance" in web_hints


def test_metabolic_liver_terms_are_anchored_to_busca2b_queries() -> None:
    taxonomy = load_json(Path("config") / "keyword_taxonomy.json")

    _, components = build_structured_components(taxonomy, "busca2b")
    clinical_terms = {term.lower() for term in components["clinical_terms"]}
    web_hints = {term.lower() for term in components["web_hints"]}
    queries = "\n".join(build_queries(taxonomy, "busca2b")).lower()

    assert "masld practice guidance" in clinical_terms
    assert "steatotic liver disease practice guidance" in clinical_terms
    assert "masld nutrition therapy" in web_hints
    assert "nafld systematic review" in web_hints
    assert "masld nutrition therapy" in queries or "nafld nutrition therapy" in queries
