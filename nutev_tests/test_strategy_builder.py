"""Question/PICOS → per-base search expressions, at three breadth levels (C4)."""
from __future__ import annotations

import pytest

from nutev.search.strategy_builder import (
    BREADTHS,
    PROVIDERS,
    Concept,
    StrategySpec,
    build_all,
    build_query,
    parse_concepts,
    parse_picos,
)


def _spec() -> StrategySpec:
    return StrategySpec(
        concepts=[
            Concept("population", ["adults", "obesity"], role="population", mesh=["Obesity"]),
            Concept("intervention", ["dietary adherence", "meal planning"], role="intervention"),
            Concept("outcome", ["weight loss"], role="outcome"),
        ],
        year_from=2015,
        year_to=2025,
        languages=["eng", "por"],
        publication_types=["Guideline"],
    )


def test_pubmed_uses_field_tags_and_mesh_and_phrase_quotes():
    q = build_query(_spec(), "pubmed", "balanced")
    assert "adults[tiab]" in q
    assert '"dietary adherence"[tiab]' in q      # multiword phrase-quoted
    assert "Obesity[Mesh]" in q                  # MeSH included
    assert " AND " in q                          # blocks AND-ed
    assert "[dp]" not in q                        # no date filter at 'balanced'


def test_pubmed_specific_adds_date_language_and_pubtype_filters():
    q = build_query(_spec(), "pubmed", "specific")
    assert '("2015"[dp] : "2025"[dp])' in q
    assert "english[lang]" in q and "portuguese[lang]" in q
    assert "Guideline[pt]" in q


def test_broad_uses_only_core_blocks():
    q = build_query(_spec(), "pubmed", "broad")
    # population + intervention are core; outcome is excluded at 'broad'.
    assert "adults[tiab]" in q
    assert '"dietary adherence"[tiab]' in q
    assert "weight loss" not in q


def test_europepmc_boolean_and_pub_year_filter():
    q = build_query(_spec(), "europepmc", "specific")
    assert "(adults OR obesity)" in q
    assert "PUB_YEAR:[2015 TO 2025]" in q
    assert "LANG:eng" in q


def test_crossref_and_openalex_are_query_plus_filter():
    cr = build_query(_spec(), "crossref", "specific")
    assert cr.startswith("query=")
    assert "from-pub-date:2015-01-01" in cr and "until-pub-date:2025-12-31" in cr
    oa = build_query(_spec(), "openalex", "specific")
    assert "from_publication_date:2015-01-01" in oa
    assert "language:eng|por" in oa


def test_build_all_covers_every_provider_and_breadth():
    grid = build_all(_spec())
    assert set(grid) == set(PROVIDERS)
    for provider in PROVIDERS:
        assert set(grid[provider]) == set(BREADTHS)
        assert all(grid[provider][b] for b in BREADTHS)


def test_parse_picos_maps_roles_and_synonyms():
    spec = parse_picos({
        "population": ["adults", "obesity"],
        "intervention": {"terms": ["diet"], "mesh": ["Diet"]},
        "outcome": "weight loss",
        "year_from": 2018,
        "languages": ["eng"],
    })
    roles = {c.role for c in spec.concepts}
    assert roles == {"population", "intervention", "outcome"}
    interv = next(c for c in spec.concepts if c.role == "intervention")
    assert interv.mesh == ["Diet"]
    assert spec.year_from == 2018


def test_parse_concepts_from_bare_lists():
    spec = parse_concepts([["diet", "nutrition"], ["adherence"]])
    assert len(spec.concepts) == 2
    q = build_query(spec, "europepmc", "balanced")
    assert "(diet OR nutrition)" in q and "(adherence)" in q


def test_unknown_provider_or_breadth_raises():
    with pytest.raises(ValueError):
        build_query(_spec(), "scopus", "balanced")
    with pytest.raises(ValueError):
        build_query(_spec(), "pubmed", "exhaustive")


def test_empty_spec_yields_empty_expression():
    assert build_query(StrategySpec(concepts=[]), "pubmed", "balanced") == ""
