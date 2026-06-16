from __future__ import annotations

from pathlib import Path

from nutev.querypacks.builders import build_structured_components
from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.settings import load_json


def _taxonomy() -> dict:
    return load_json(Path("config/keyword_taxonomy.json"))


def test_busca1_structured_components_include_food_access_program_variants() -> None:
    _, components = build_structured_components(_taxonomy(), "busca1")

    for term in [
        "healthy food incentive",
        "produce voucher",
        "medically tailored pantry",
        "medically tailored food packages",
        "food farmacy intervention",
        "food farmacy implementation",
    ]:
        assert term in components["focus_terms"]
        assert term in components["web_hints"]


def test_busca2b_structured_components_include_food_access_program_variants() -> None:
    _, components = build_structured_components(_taxonomy(), "busca2b")

    for term in [
        "food prescription program",
        "healthy food prescription",
        "nutrition incentives",
        "fruit and vegetable vouchers",
        "food farmacy intervention",
        "food farmacy implementation",
    ]:
        assert term in components["focus_terms"]
        assert term in components["web_hints"]


def test_busca2b_provider_queries_surface_new_food_access_variants() -> None:
    queries = render_queries_for_provider(_taxonomy(), "busca2b", "openalex")
    joined_queries = " ".join(queries).lower()

    assert "healthy food incentive" in joined_queries
    assert "produce voucher" in joined_queries
    assert "medically tailored pantry" in joined_queries
    assert "food farmacy intervention" in joined_queries
    assert "food farmacy implementation" in joined_queries
