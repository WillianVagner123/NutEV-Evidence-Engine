from __future__ import annotations

import json
from pathlib import Path

from tools.inventory_article2_legacy_runtime import build_inventory


def _write_candidate(root: Path, name: str = "project_output_legacy") -> Path:
    candidate = root / name
    candidate.mkdir(parents=True)
    (candidate / "paper.txt").write_text("candidate bytes", encoding="utf-8")
    (candidate / "AUDIT_MANIFEST.json").write_text(
        json.dumps(
            {
                "record_type": "NUTEV_TEST_MANIFEST",
                "schema_version": 1,
                "article_scope": "A2",
                "record_count": 2827,
                "search_id": "private-search-id-must-not-leak",
                "query": "private query text must not leak",
            }
        ),
        encoding="utf-8",
    )
    return candidate


def test_inventory_is_deterministic_read_only_and_does_not_expose_paths_or_queries(tmp_path: Path) -> None:
    root = tmp_path / "runtime"
    candidate = _write_candidate(root)
    watched = candidate / "paper.txt"
    before_bytes = watched.read_bytes()
    before_mtime = watched.stat().st_mtime_ns

    first = build_inventory([root], max_depth=2)
    second = build_inventory([root], max_depth=2)

    assert first["status"] == "PASS"
    assert first["read_only"] is True
    assert first["scientific_state_modified"] is False
    assert first["legacy_binding_performed"] is False
    assert first["search_executed"] is False
    assert first["ownership_inferred_from_names"] is False
    assert first["binding_status"] == "NOT_CREATED_REVIEW_REQUIRED"
    assert first["candidate_count"] == 1
    assert first["inventory_sha256"] == second["inventory_sha256"]

    item = first["candidates"][0]
    assert item["ownership"] == "UNKNOWN_UNTIL_REVIEW"
    assert item["classification_inferred"] is False
    assert item["raw_path_exposed"] is False
    assert item["query_text_exposed"] is False
    assert item["search_id_exposed"] is False
    assert len(item["tree_sha256"]) == 64
    assert item["source_fingerprint"] == item["tree_sha256"]
    assert item["file_count"] == 2

    metadata = item["safe_manifest_metadata"][0]["safe_metadata"]
    assert metadata["record_type"] == "NUTEV_TEST_MANIFEST"
    assert metadata["article_scope"] == "A2"
    assert metadata["record_count"] == 2827

    rendered = json.dumps(first, ensure_ascii=False)
    assert str(candidate) not in rendered
    assert "private-search-id-must-not-leak" not in rendered
    assert "private query text must not leak" not in rendered

    assert watched.read_bytes() == before_bytes
    assert watched.stat().st_mtime_ns == before_mtime


def test_content_fingerprint_is_content_based_while_candidate_identity_is_location_scoped(tmp_path: Path) -> None:
    root_a = tmp_path / "a"
    root_b = tmp_path / "b"
    first_path = _write_candidate(root_a, "project_output_one")
    second_path = _write_candidate(root_b, "project_output_two")

    report = build_inventory([first_path, second_path], max_depth=0)
    assert report["candidate_count"] == 2

    first, second = report["candidates"]
    assert first["candidate_id"] != second["candidate_id"]
    assert first["location_fingerprint_sha256"] != second["location_fingerprint_sha256"]
    assert first["source_fingerprint"] == second["source_fingerprint"]


def test_missing_or_unmatched_roots_do_not_invent_candidates(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    unrelated = empty / "not_a_candidate"
    unrelated.mkdir()
    (unrelated / "file.txt").write_text("x", encoding="utf-8")

    report = build_inventory([empty, tmp_path / "missing"], max_depth=2)

    assert report["status"] == "PASS"
    assert report["candidate_count"] == 0
    assert report["candidates"] == []
    assert report["legacy_binding_performed"] is False
