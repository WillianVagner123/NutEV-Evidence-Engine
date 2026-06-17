from __future__ import annotations

from pathlib import Path

from nutev.querypacks.builders import build_structured_components
from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.settings import load_json


def _taxonomy() -> dict:
    return load_json(Path("config") / "keyword_taxonomy.json")


def test_ckm_terms_are_loaded_for_clinical_workstreams() -> None:
    taxonomy = _taxonomy()

    for workstream in ("busca2a", "busca2b"):
        _, components = build_structured_components(taxonomy, workstream)
        condition_terms = {term.lower() for term in components["condition_terms"]}
        outcome_terms = {term.lower() for term in components["priority_outcomes"]}

        assert "ckm syndrome" in condition_terms
        assert "cardiovascular-kidney-metabolic syndrome" in condition_terms
        assert "chronic kidney disease" in condition_terms
        assert "cardiovascular-kidney-metabolic outcomes" in outcome_terms
        assert "albuminuria" in outcome_terms


def test_ckm_terms_reach_provider_queries() -> None:
    taxonomy = _taxonomy()

    for workstream in ("busca2a", "busca2b"):
        pubmed_queries = "\n".join(render_queries_for_provider(taxonomy, workstream, "pubmed")).lower()
        europepmc_queries = "\n".join(render_queries_for_provider(taxonomy, workstream, "europepmc")).lower()

        assert "ckm syndrome" in pubmed_queries
        assert "cardiovascular-kidney-metabolic syndrome" in pubmed_queries
        assert "chronic kidney disease" in pubmed_queries
        assert "ckm syndrome" in europepmc_queries
        assert "cardiovascular-kidney-metabolic syndrome" in europepmc_queries
        assert "chronic kidney disease" in europepmc_queries
