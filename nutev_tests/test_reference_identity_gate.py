from __future__ import annotations

import importlib.util
from pathlib import Path

from nutev.audit_guardrails import annotate_record
from nutev.reference_identity import canonical_identity, dedupe_records


ROOT = Path(__file__).resolve().parents[1]


def _load_tool(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_doi_url_and_plain_doi_share_identity() -> None:
    plain = canonical_identity({"doi": "10.1000/ABC.DEF", "title": "One"})
    as_url = canonical_identity(
        {"doi": "https://doi.org/10.1000/abc.def", "title": "Different"}
    )
    assert plain == as_url == "doi:10.1000/abc.def"


def test_malformed_pmid_is_not_silently_repaired() -> None:
    row = {"pmid": "12A45", "title": "Fallback Title"}
    assert canonical_identity(row) == "title:fallback title"


def test_http_url_is_normalized_before_title_fallback() -> None:
    first = canonical_identity(
        {"url": "HTTPS://WWW.Example.org/path/#fragment", "title": "A"}
    )
    second = canonical_identity(
        {"url": "https://example.org/path", "title": "B"}
    )
    assert first == second == "url:https://example.org/path"


def test_collection_and_ranking_use_same_identity_contract() -> None:
    collection = _load_tool("collection_gate_test", "tools/run_everything_now.py")
    ranking = _load_tool("ranking_gate_test", "tools/rank_references.py")
    row = {
        "doi": "https://doi.org/10.1000/Example",
        "pmid": "12A45",
        "url": "https://www.example.org/reference/",
        "title": "Example Reference",
    }
    expected = canonical_identity(row)
    assert collection._identity(row) == expected
    assert ranking._identity(row) == expected


def test_shared_dedupe_prefers_richer_record() -> None:
    rows = [
        {
            "doi": "10.1000/example",
            "title": "Short",
            "abstract": "short",
        },
        {
            "doi": "https://doi.org/10.1000/EXAMPLE",
            "title": "Richer manifestation",
            "abstract": "a much richer abstract for the same record",
        },
    ]
    unique = dedupe_records(rows)
    assert len(unique) == 1
    assert unique[0]["title"] == "Richer manifestation"


def test_shared_dedupe_preserves_all_observed_provider_manifestations() -> None:
    rows = [
        {
            "source_provider": "pubmed",
            "source": "pubmed",
            "doi": "10.1000/example",
            "pmid": "12345678",
            "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
            "title": "Same article",
            "abstract": "short",
            "provider_query": "creatine cognition older adults",
            "query_dialect": "pubmed",
            "interactive_retrieved_at": "2026-09-07T01:00:00Z",
        },
        {
            "source_provider": "crossref",
            "source": "crossref",
            "doi": "https://doi.org/10.1000/EXAMPLE",
            "url": "https://doi.org/10.1000/example",
            "title": "Same article",
            "abstract": "a richer abstract from Crossref for the same article",
            "provider_query": "creatine cognition older adults",
            "query_dialect": "crossref",
            "interactive_retrieved_at": "2026-09-07T01:00:01Z",
        },
    ]

    unique = dedupe_records(rows)
    assert len(unique) == 1
    record = unique[0]
    assert record["source_provider"] == "crossref"
    assert record["source_providers"] == ["crossref", "pubmed"]
    assert [item["provider"] for item in record["source_manifestations"]] == [
        "crossref",
        "pubmed",
    ]
    pubmed = next(item for item in record["source_manifestations"] if item["provider"] == "pubmed")
    assert pubmed["pmid"] == "12345678"
    assert pubmed["provider_query"] == "creatine cognition older adults"
    assert pubmed["url"] == "https://pubmed.ncbi.nlm.nih.gov/12345678"


def test_dedupe_provenance_is_idempotent_and_does_not_multiply_manifestations() -> None:
    rows = [
        {
            "source_provider": "pubmed",
            "doi": "10.1000/example",
            "title": "Article",
            "abstract": "abstract",
            "provider_query": "query one",
        },
        {
            "source_provider": "europepmc",
            "doi": "10.1000/example",
            "title": "Article",
            "abstract": "abstract",
            "provider_query": "query two",
        },
    ]
    once = dedupe_records(rows)
    twice = dedupe_records(once)
    assert once == twice
    assert len(twice[0]["source_manifestations"]) == 2
    assert twice[0]["source_providers"] == ["europepmc", "pubmed"]


def test_provider_multiplicity_is_provenance_only_not_a_scientific_score_signal() -> None:
    ranking = _load_tool("ranking_provenance_only_test", "tools/rank_references.py")
    base = annotate_record(
        {
            "title": "Traceable reference",
            "abstract": "nutrition evidence",
            "source_provider": "crossref",
            "doi": "10.1000/example",
        }
    )
    multi = dict(base)
    multi["source_providers"] = ["crossref", "pubmed", "europepmc"]
    multi["source_manifestations"] = [
        {"provider": "crossref", "doi": "10.1000/example"},
        {"provider": "pubmed", "doi": "10.1000/example"},
        {"provider": "europepmc", "doi": "10.1000/example"},
    ]
    assert ranking.score_record(base, {}, [], {})["reference_score"] == ranking.score_record(
        multi, {}, [], {}
    )["reference_score"]


def test_invalid_identifier_with_url_gets_no_identifier_bonus() -> None:
    ranking = _load_tool("ranking_score_gate_test", "tools/rank_references.py")
    row = annotate_record(
        {
            "title": "Traceable by URL",
            "abstract": "x",
            "source_provider": "crossref",
            "doi": "not-a-doi",
            "url": "https://example.org/reference/1",
        }
    )
    assert row["audit_traceability"] == "B_TRACEABLE_URL"
    scored = ranking.score_record(row, {}, [], {})
    assert scored["score_breakdown"]["identifier"] == 0.0


def test_valid_identifier_keeps_identifier_bonus() -> None:
    ranking = _load_tool("ranking_valid_identifier_test", "tools/rank_references.py")
    row = annotate_record(
        {
            "title": "Traceable by DOI",
            "abstract": "x",
            "source_provider": "crossref",
            "doi": "10.1000/example",
        }
    )
    assert row["audit_traceability"] == "A_IDENTIFIER"
    scored = ranking.score_record(row, {}, [], {})
    assert scored["score_breakdown"]["identifier"] == 2.0
