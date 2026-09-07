from __future__ import annotations

import json
import sqlite3

from nutev.registry import SQLiteArticleRegistry


def _registry(tmp_path):
    return SQLiteArticleRegistry(tmp_path / "registry" / "article_registry.sqlite")


def test_same_doi_different_metadata_is_one_article_with_two_manifestations(tmp_path) -> None:
    registry = _registry(tmp_path)
    first = registry.register_article(
        {
            "source_provider": "crossref",
            "doi": "https://doi.org/10.1000/ABC",
            "title": "Observed title",
            "abstract": "short",
        }
    )
    second = registry.register_article(
        {
            "source_provider": "pubmed",
            "doi": "10.1000/abc",
            "title": "Provider title variant",
            "abstract": "a substantially longer observed abstract from another provider",
        }
    )

    assert first.status == "CREATED"
    assert second.status == "ENRICHED"
    assert first.article_id == second.article_id
    assert registry.stats().articles == 1
    assert registry.stats().manifestations == 2
    article = registry.get_article(first.article_id or "")
    assert article is not None
    assert article["manifestation_count"] == 2
    assert article["abstract"].startswith("a substantially longer")


def test_pmid_then_doi_plus_pmid_enriches_same_global_identity(tmp_path) -> None:
    registry = _registry(tmp_path)
    first = registry.register_article(
        {"source_provider": "pubmed", "pmid": "12345678", "title": "Bridge"}
    )
    second = registry.register_article(
        {
            "source_provider": "europepmc",
            "pmid": "12345678",
            "doi": "10.1000/bridge",
            "title": "Bridge",
        }
    )

    assert first.article_id == second.article_id
    assert registry.stats().articles == 1
    article = registry.get_article(first.article_id or "")
    assert article is not None
    assert {(row["scheme"], row["normalized_value"]) for row in article["aliases"]} >= {
        ("pmid", "12345678"),
        ("doi", "10.1000/bridge"),
    }


def test_pmcid_pmid_and_doi_accumulate_on_one_article(tmp_path) -> None:
    registry = _registry(tmp_path)
    first = registry.register_article(
        {"source_provider": "europepmc", "pmcid": "PMC1234567", "title": "PMC bridge"}
    )
    second = registry.register_article(
        {
            "source_provider": "pubmed",
            "pmcid": "PMC1234567",
            "pmid": "87654321",
            "title": "PMC bridge",
        }
    )
    third = registry.register_article(
        {
            "source_provider": "crossref",
            "pmid": "87654321",
            "doi": "10.1000/pmc-bridge",
            "title": "PMC bridge",
        }
    )

    assert first.article_id == second.article_id == third.article_id
    assert registry.stats().articles == 1
    assert registry.stats().aliases == 3


def test_same_title_with_different_dois_stays_two_articles(tmp_path) -> None:
    registry = _registry(tmp_path)
    left = registry.register_article(
        {"source_provider": "crossref", "doi": "10.1000/left", "title": "Same title"}
    )
    right = registry.register_article(
        {"source_provider": "pubmed", "doi": "10.1000/right", "title": "Same title"}
    )

    assert left.article_id != right.article_id
    assert registry.stats().articles == 2
    assert registry.stats().identity_conflicts_open == 0


def test_similar_unidentified_titles_are_not_fuzzy_merged(tmp_path) -> None:
    registry = _registry(tmp_path)
    left = registry.register_article(
        {
            "source_provider": "doaj",
            "title": "Nutrition literacy in older adults",
            "year": 2025,
            "journal": "Journal A",
        }
    )
    right = registry.register_article(
        {
            "source_provider": "crossref",
            "title": "Nutrition literacy among older adults",
            "year": 2025,
            "journal": "Journal A",
        }
    )

    assert left.article_id != right.article_id
    assert registry.stats().articles == 2


def test_conflicting_strong_identifiers_are_quarantined_not_merged(tmp_path) -> None:
    registry = _registry(tmp_path)
    left = registry.register_article(
        {
            "source_provider": "pubmed",
            "pmid": "12345678",
            "doi": "10.1000/left",
            "title": "Left",
        }
    )
    conflict = registry.register_article(
        {
            "source_provider": "crossref",
            "pmid": "12345678",
            "doi": "10.1000/right",
            "title": "Right",
        }
    )

    assert left.article_id is not None
    assert conflict.status == "CONFLICT"
    assert conflict.conflict_id is not None
    assert conflict.article_id is not None
    assert conflict.article_id != left.article_id
    assert registry.stats().articles == 2
    assert registry.stats().identity_conflicts_open == 1
    assert registry.get_article(left.article_id)["registry_status"] == "identity_conflict"
    assert registry.get_article(conflict.article_id)["registry_status"] == "identity_conflict"


def test_repeated_ingestion_is_idempotent(tmp_path) -> None:
    registry = _registry(tmp_path)
    record = {
        "source_provider": "pubmed",
        "doi": "10.1000/idempotent",
        "pmid": "55556666",
        "title": "Idempotent article",
        "abstract": "stable abstract",
    }
    first = registry.register_article(record)
    before = registry.stats()
    second = registry.register_article(record)
    after = registry.stats()

    assert first.status == "CREATED"
    assert second.status == "MATCHED"
    assert first.article_id == second.article_id
    assert after.articles == before.articles == 1
    assert after.aliases == before.aliases == 2
    assert after.manifestations == before.manifestations == 1


def test_registry_survives_reopen_with_same_article_ids(tmp_path) -> None:
    path = tmp_path / "registry" / "article_registry.sqlite"
    registry = SQLiteArticleRegistry(path)
    created = registry.register_article(
        {"source_provider": "pubmed", "pmid": "11223344", "title": "Persistent"}
    )

    reopened = SQLiteArticleRegistry(path)
    assert reopened.stats().articles == 1
    assert reopened.get_article(created.article_id or "") is not None
    assert reopened.integrity_check() == "ok"


def test_canonical_field_updates_are_audited_with_explicit_precedence(tmp_path) -> None:
    registry = _registry(tmp_path)
    created = registry.register_article(
        {
            "source_provider": "crossref",
            "doi": "10.1000/history",
            "title": "Stable canonical title",
            "abstract": "short",
        }
    )
    registry.register_article(
        {
            "source_provider": "pubmed",
            "doi": "10.1000/history",
            "title": "Different provider title",
            "abstract": "a longer observed abstract that should enrich but not replace the first title",
        }
    )

    article = registry.get_article(created.article_id or "")
    assert article is not None
    assert article["canonical_title"] == "Stable canonical title"
    assert article["abstract"].startswith("a longer observed abstract")

    connection = sqlite3.connect(registry.database_path)
    try:
        rules = {
            row[0]
            for row in connection.execute(
                "SELECT precedence_rule FROM article_field_history WHERE article_id = ?",
                (created.article_id,),
            ).fetchall()
        }
    finally:
        connection.close()
    assert "first_observed" in rules
    assert "prefer_longer_observed_abstract" in rules


def test_registry_schema_manifest_and_integrity_gate(tmp_path) -> None:
    registry = _registry(tmp_path)
    registry.register_article(
        {"source_provider": "pubmed", "pmid": "99887766", "title": "Integrity"}
    )

    assert registry.integrity_check() == "ok"
    manifest = json.loads(registry.manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "PASS"
    assert manifest["counts"]["articles"] == 1
    assert manifest["guardrails"]["registry_presence_is_not_scientific_inclusion"] is True

    connection = sqlite3.connect(registry.database_path)
    try:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
    finally:
        connection.close()
    assert {
        "articles",
        "article_aliases",
        "article_manifestations",
        "article_field_history",
        "search_runs",
        "search_hits",
        "identity_conflicts",
    } <= tables
