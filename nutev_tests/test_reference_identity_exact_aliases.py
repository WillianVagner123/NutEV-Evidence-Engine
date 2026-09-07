from __future__ import annotations

from nutev.reference_identity import canonical_identity, dedupe_records


def _row(provider: str, **values: object) -> dict[str, object]:
    return {"source_provider": provider, **values}


def test_doi_plus_pmid_bridges_to_pmid_only_manifestation() -> None:
    rows = [
        _row(
            "pubmed",
            doi="10.1000/bridge",
            pmid="12345678",
            title="Bridge article",
            abstract="short",
        ),
        _row(
            "europepmc",
            pmid="12345678",
            title="Bridge article from Europe PMC",
            abstract="a richer abstract retained as the descriptive manifestation",
        ),
    ]

    unique = dedupe_records(rows)
    assert len(unique) == 1
    assert unique[0]["source_providers"] == ["europepmc", "pubmed"]
    assert {item.get("doi") for item in unique[0]["source_manifestations"] if item.get("doi")} == {
        "10.1000/bridge"
    }
    assert {item.get("pmid") for item in unique[0]["source_manifestations"] if item.get("pmid")} == {
        "12345678"
    }


def test_doi_plus_url_bridges_to_url_only_manifestation() -> None:
    rows = [
        _row(
            "crossref",
            doi="10.1000/url-bridge",
            url="https://example.org/article/42",
            title="URL bridge",
        ),
        _row(
            "openalex",
            url="https://www.example.org/article/42/",
            title="Different provider title",
        ),
    ]

    unique = dedupe_records(rows)
    assert len(unique) == 1
    assert unique[0]["source_providers"] == ["crossref", "openalex"]


def test_pmid_plus_pmcid_bridges_to_pmcid_only_even_without_title() -> None:
    rows = [
        _row(
            "pubmed",
            pmid="87654321",
            pmcid="PMC1234567",
            title="PMC bridge",
        ),
        _row("europepmc", pmcid="PMC1234567"),
    ]

    unique = dedupe_records(rows)
    assert len(unique) == 1
    assert unique[0]["source_providers"] == ["europepmc", "pubmed"]
    # Public canonical identity remains unchanged: PMCID is an internal exact alias, not a new public key.
    assert canonical_identity({"pmcid": "PMC1234567"}) == ""


def test_exact_bridge_can_merge_two_previously_separate_identifier_groups() -> None:
    rows = [
        _row("crossref", doi="10.1000/three-way", title="DOI manifestation"),
        _row("pubmed", pmid="11122233", title="PMID manifestation"),
        _row(
            "europepmc",
            doi="10.1000/three-way",
            pmid="11122233",
            title="Bridge manifestation",
            abstract="the bridge explicitly carries both exact identifiers",
        ),
    ]

    unique = dedupe_records(rows)
    assert len(unique) == 1
    assert unique[0]["source_providers"] == ["crossref", "europepmc", "pubmed"]


def test_same_pmid_with_conflicting_dois_stays_separate() -> None:
    rows = [
        _row("pubmed", pmid="12345678", doi="10.1000/left", title="Left"),
        _row("crossref", pmid="12345678", doi="10.1000/right", title="Right"),
    ]

    unique = dedupe_records(rows)
    assert len(unique) == 2
    assert {record.get("doi") for record in unique} == {"10.1000/left", "10.1000/right"}


def test_ambiguous_pmid_does_not_force_sparse_future_row_into_first_conflict_group() -> None:
    rows = [
        _row("pubmed", pmid="12345678", doi="10.1000/left", title="Left"),
        _row("crossref", pmid="12345678", doi="10.1000/right", title="Right"),
        _row("europepmc", pmid="12345678", title="Sparse ambiguous manifestation"),
    ]

    unique = dedupe_records(rows)
    assert len(unique) == 3
    assert sorted(record.get("source_provider") for record in unique) == [
        "crossref",
        "europepmc",
        "pubmed",
    ]


def test_same_doi_with_conflicting_pmids_stays_separate() -> None:
    rows = [
        _row("pubmed", doi="10.1000/shared", pmid="11111111", title="Left"),
        _row("crossref", doi="10.1000/shared", pmid="22222222", title="Right"),
    ]

    unique = dedupe_records(rows)
    assert len(unique) == 2
    assert {record.get("pmid") for record in unique} == {"11111111", "22222222"}


def test_shared_url_cannot_override_conflicting_strong_identifiers() -> None:
    rows = [
        _row(
            "pubmed",
            doi="10.1000/url-left",
            url="https://example.org/shared",
            title="Left",
        ),
        _row(
            "crossref",
            doi="10.1000/url-right",
            url="https://www.example.org/shared/",
            title="Right",
        ),
    ]

    unique = dedupe_records(rows)
    assert len(unique) == 2


def test_exact_title_fallback_still_merges_unidentified_records() -> None:
    rows = [
        _row("doaj", title="  Nutrition   Literacy in Older Adults  ", abstract="short"),
        _row(
            "crossref",
            title="nutrition literacy in older adults",
            abstract="a richer abstract for the same exact normalized title",
        ),
    ]

    unique = dedupe_records(rows)
    assert len(unique) == 1
    assert unique[0]["source_providers"] == ["crossref", "doaj"]


def test_similar_title_is_not_fuzzy_merged() -> None:
    rows = [
        _row("doaj", title="Nutrition literacy in older adults"),
        _row("crossref", title="Nutrition literacy among older adults"),
    ]

    assert len(dedupe_records(rows)) == 2


def test_identified_records_do_not_merge_merely_because_titles_match() -> None:
    rows = [
        _row("pubmed", pmid="11111111", title="Identical title"),
        _row("crossref", doi="10.1000/different", title="Identical title"),
    ]

    assert len(dedupe_records(rows)) == 2


def test_aliases_retained_in_manifestations_can_bridge_later_dedupe_pass() -> None:
    first_pass = dedupe_records(
        [
            _row(
                "crossref",
                doi="10.1000/persisted-alias",
                pmid="33334444",
                title="Primary with DOI",
                abstract="short",
            ),
            _row(
                "pubmed",
                pmid="33334444",
                title="Richer PMID manifestation",
                abstract="a much richer abstract that wins but has no top-level DOI",
            ),
        ]
    )
    assert len(first_pass) == 1
    assert not first_pass[0].get("doi")

    second_pass = dedupe_records(
        [
            first_pass[0],
            _row("openalex", doi="10.1000/persisted-alias", title="Later DOI-only record"),
        ]
    )
    assert len(second_pass) == 1
    assert second_pass[0]["source_providers"] == ["crossref", "openalex", "pubmed"]


def test_exact_alias_deduplication_is_idempotent() -> None:
    rows = [
        _row("crossref", doi="10.1000/idempotent", title="DOI"),
        _row("pubmed", pmid="55556666", title="PMID"),
        _row(
            "europepmc",
            doi="10.1000/idempotent",
            pmid="55556666",
            title="Bridge",
        ),
    ]

    once = dedupe_records(rows)
    twice = dedupe_records(once)
    assert once == twice
