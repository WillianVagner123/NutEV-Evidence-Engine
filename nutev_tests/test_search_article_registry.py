from __future__ import annotations

import copy
import json
from pathlib import Path
import sqlite3
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = REPO_ROOT / "apps" / "nutev-web"
if str(WEB_ROOT) not in sys.path:
    sys.path.insert(0, str(WEB_ROOT))

from nutev.registry.ingest import SearchRegistryIngestor, register_search_result

import search_adapter


def _row(index: int, *, provider: str = "pubmed") -> dict:
    return {
        "title": f"Article {index}",
        "doi": f"10.1000/article-{index}",
        "source_provider": provider,
        "source": provider,
        "provider_query": "nutrition",
        "interactive_retrieved_at": "2026-09-07T12:00:00+00:00",
        "reference_rank": index + 1,
        "reference_score": float(100 - (index % 50)),
        "query_relevance_score": float(90 - (index % 20)),
        "nutev_priority_score": float(70 - (index % 10)),
    }


def _result(search_id: str, indexes: range, *, provider: str = "pubmed") -> dict:
    rows = [_row(index, provider=provider) for index in indexes]
    return {
        "schema_version": 3,
        "search_id": search_id,
        "query": "nutrition",
        "created_at": "2026-09-07T12:00:00+00:00",
        "search_mode": "global_exhaustive",
        "status": "COMPLETE",
        "providers": [
            {
                "provider": provider,
                "status": "completed",
                "returned": len(rows),
                "total_found": len(rows),
            }
        ],
        "failed_providers": [],
        "unavailable_providers": [],
        "non_exhaustive_providers": [],
        "audit_gaps": [],
        "records_before_dedup": len(rows),
        "unique_records": len(rows),
        "returned_records": len(rows),
        "results": rows,
    }


def _registry(root: Path) -> SearchRegistryIngestor:
    registry_root = root / "registry"
    return SearchRegistryIngestor(
        registry_root / "article_registry.sqlite",
        registry_root / "ARTICLE_REGISTRY_MANIFEST.json",
    )


def test_overlapping_searches_accumulate_articles_without_replacement(tmp_path: Path) -> None:
    first = _result("web_search_a", range(0, 100), provider="pubmed")
    second = _result("web_search_b", range(70, 150), provider="crossref")

    register_search_result(first, output_root=tmp_path)
    assert first["registry_summary"]["registry_created"] == 100
    assert first["registry_summary"]["articles_after"] == 100

    register_search_result(second, output_root=tmp_path)
    assert second["registry_summary"]["registry_created"] == 50
    assert second["registry_summary"]["registry_matches"] == 30
    assert second["registry_summary"]["articles_before"] == 100
    assert second["registry_summary"]["articles_after"] == 150
    assert second["registry_summary"]["article_count_delta"] == 50

    registry = _registry(tmp_path)
    stats = registry.stats()
    assert stats.articles == 150
    assert stats.search_runs == 2
    assert stats.search_hits == 180
    assert registry.integrity_check() == "ok"


def test_reprocessing_same_search_is_idempotent_for_articles_and_hits(tmp_path: Path) -> None:
    result = _result("web_repeat", range(0, 80))
    register_search_result(result, output_root=tmp_path)
    first_ids = [row["article_id"] for row in result["results"]]
    before = _registry(tmp_path).stats()

    replay = copy.deepcopy(result)
    replay.pop("registry_summary", None)
    for row in replay["results"]:
        row.pop("registry_identity_status", None)
    register_search_result(replay, output_root=tmp_path)

    after = _registry(tmp_path).stats()
    assert [row["article_id"] for row in replay["results"]] == first_ids
    assert after.articles == before.articles == 80
    assert after.search_runs == before.search_runs == 1
    assert after.search_hits == before.search_hits == 80
    assert replay["registry_summary"]["registry_created"] == 0
    assert replay["registry_summary"]["article_count_delta"] == 0


def test_registry_survives_restart_and_keeps_global_article_ids(tmp_path: Path) -> None:
    result = _result("web_restart", range(0, 12))
    register_search_result(result, output_root=tmp_path)
    article_ids = [row["article_id"] for row in result["results"]]

    reopened = _registry(tmp_path)
    assert reopened.stats().articles == 12
    assert reopened.integrity_check() == "ok"
    assert all(reopened.get_article(article_id) for article_id in article_ids)


def test_provider_manifestations_become_search_hits_for_one_global_article(tmp_path: Path) -> None:
    row = _row(1)
    row["source_manifestations"] = [
        {
            "source_provider": "pubmed",
            "source": "pubmed",
            "doi": "10.1000/article-1",
            "pmid": "12345678",
            "provider_query": "nutrition",
        },
        {
            "source_provider": "openalex",
            "source": "openalex",
            "doi": "https://doi.org/10.1000/ARTICLE-1",
            "openalex_id": "https://openalex.org/W123456789",
            "provider_query": "nutrition",
        },
    ]
    result = _result("web_multi_provider", range(0, 0))
    result["results"] = [row]
    result["records_before_dedup"] = 2
    result["unique_records"] = 1
    result["returned_records"] = 1

    register_search_result(result, output_root=tmp_path)

    assert result["results"][0]["article_id"].startswith("NUTEV-ART-")
    registry = _registry(tmp_path)
    assert registry.stats().articles == 1
    assert registry.stats().search_hits == 2
    article = registry.get_article(result["results"][0]["article_id"])
    assert article is not None
    aliases = {(item["scheme"], item["normalized_value"]) for item in article["aliases"]}
    assert ("doi", "10.1000/article-1") in aliases
    assert ("pmid", "12345678") in aliases
    assert ("openalex", "w123456789") in aliases


def test_search_rank_stays_contextual_in_search_hits_not_article_identity(tmp_path: Path) -> None:
    first = _result("web_rank_a", range(0, 1))
    first["results"][0]["reference_rank"] = 1
    second = _result("web_rank_b", range(0, 1), provider="crossref")
    second["results"][0]["reference_rank"] = 47

    register_search_result(first, output_root=tmp_path)
    register_search_result(second, output_root=tmp_path)

    assert first["results"][0]["article_id"] == second["results"][0]["article_id"]
    connection = sqlite3.connect(tmp_path / "registry" / "article_registry.sqlite")
    try:
        ranks = [
            row[0]
            for row in connection.execute(
                "SELECT reference_rank FROM search_hits ORDER BY search_id"
            ).fetchall()
        ]
        article_columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(articles)").fetchall()
        }
    finally:
        connection.close()
    assert ranks == [1, 47]
    assert "reference_rank" not in article_columns
    assert "reference_score" not in article_columns


def test_persist_search_registers_article_ids_before_writing_result_json(tmp_path: Path) -> None:
    result = _result("web_persist", range(0, 3))

    search_adapter._persist_search(result, tmp_path)

    saved = json.loads(
        (tmp_path / "15_web_searches" / "web_persist" / "result.json").read_text(
            encoding="utf-8"
        )
    )
    assert saved["registry_summary"]["status"] == "COMPLETE"
    assert saved["registry_summary"]["registry_created"] == 3
    assert all(row["article_id"].startswith("NUTEV-ART-") for row in saved["results"])
    assert (tmp_path / "registry" / "article_registry.sqlite").is_file()


def test_second_persist_after_full_text_does_not_reingest_or_change_summary(tmp_path: Path) -> None:
    result = _result("web_fulltext_rewrite", range(0, 2))
    search_adapter._persist_search(result, tmp_path)
    first_summary = copy.deepcopy(result["registry_summary"])
    first_stats = _registry(tmp_path).stats()

    result["results"][0]["full_text"] = {
        "status": "extracted",
        "ocr_used": True,
        "ranking_influence": "none",
    }
    search_adapter._persist_search(result, tmp_path)

    second_stats = _registry(tmp_path).stats()
    assert result["registry_summary"] == first_summary
    assert second_stats.articles == first_stats.articles
    assert second_stats.manifestations == first_stats.manifestations
    assert second_stats.search_hits == first_stats.search_hits


def test_registry_failure_is_explicit_without_invalidating_search(monkeypatch, tmp_path: Path) -> None:
    result = _result("web_registry_failure", range(0, 1))

    def explode(*_args, **_kwargs):
        raise RuntimeError("synthetic registry failure")

    monkeypatch.setattr(search_adapter, "register_search_result", explode)
    search_adapter._persist_search(result, tmp_path)

    assert result["status"] == "COMPLETE"
    assert result["registry_summary"]["status"] == "FAILED"
    assert result["registry_summary"]["search_result_still_valid"] is True
    saved = json.loads(
        (tmp_path / "15_web_searches" / "web_registry_failure" / "result.json").read_text(
            encoding="utf-8"
        )
    )
    assert saved["registry_summary"]["status"] == "FAILED"


def test_identity_conflict_is_idempotent_when_search_is_reprocessed(tmp_path: Path) -> None:
    left = _result("web_conflict_left", range(0, 0))
    left["results"] = [
        {
            "title": "Left",
            "source_provider": "pubmed",
            "pmid": "12345678",
            "doi": "10.1000/left",
            "provider_query": "nutrition",
            "reference_rank": 1,
        }
    ]
    left["returned_records"] = left["unique_records"] = left["records_before_dedup"] = 1
    register_search_result(left, output_root=tmp_path)

    conflicting = _result("web_conflict_right", range(0, 0))
    conflicting["results"] = [
        {
            "title": "Right",
            "source_provider": "crossref",
            "pmid": "12345678",
            "doi": "10.1000/right",
            "provider_query": "nutrition",
            "reference_rank": 1,
        }
    ]
    conflicting["returned_records"] = conflicting["unique_records"] = conflicting[
        "records_before_dedup"
    ] = 1
    register_search_result(conflicting, output_root=tmp_path)
    registry = _registry(tmp_path)
    assert registry.stats().identity_conflicts_open == 1

    replay = copy.deepcopy(conflicting)
    replay.pop("registry_summary", None)
    register_search_result(replay, output_root=tmp_path)
    assert _registry(tmp_path).stats().identity_conflicts_open == 1
